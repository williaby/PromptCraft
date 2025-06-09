// Bicep template for deploying Azure resources for a chatbot solution
targetScope = 'resourceGroup'

// PARAMETERS
@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Storage account name (3–24 lowercase letters/numbers)')
@minLength(3)
@maxLength(24)
param storageAccountName string

@description('Cognitive Search service name (1–60 chars)')
@minLength(1)
@maxLength(60)
param cognitiveSearchName string

@description('Azure OpenAI account name (3–24 chars)')
@minLength(3)
@maxLength(24)
param openAiName string

@description('App Service plan name')
param appServicePlanName string

@description('Function App name')
param functionAppName string

@description('Key Vault name')
param keyVaultName string

@description('Bot Service name')
param botServiceName string

@description('Virtual Network name')
param vnetName string

@description('Default subnet name')
param defaultSubnetName string = 'default'

@description('Private endpoints subnet name')
param peSubnetName string = 'private-endpoints'

// 1. VNET MODULE
module vnetModule 'modules/vnet.bicep' = {
  name: 'deployVnet'
  params: {
    vnetName:          vnetName
    location:         location
    defaultSubnetName: defaultSubnetName
    defaultSubnetPrefix: '10.0.0.0/24'
    peSubnetName:      peSubnetName
    peSubnetPrefix:    '10.0.1.0/24'
  }
}

var defaultSubnetId = vnetModule.outputs.defaultSubnetId
var peSubnetId      = vnetModule.outputs.peSubnetId

// 2. STORAGE ACCOUNT
resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: toLower(storageAccountName)
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
}

// 3. COGNITIVE SEARCH
resource searchService 'Microsoft.Azure.Search/searchServices@2021-04-01' = {
  name: cognitiveSearchName
  location: location
  sku: { name: 'standard'; tier: 'standard' }
  properties: {
    hostingMode:    'default'
    replicaCount:   1
    partitionCount: 1
  }
}

// 4. AZURE OPENAI
resource openAi 'Microsoft.CognitiveServices/accounts@2022-12-01' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: { customSubDomainName: openAiName }
}

// 5. APP SERVICE PLAN
resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: appServicePlanName
  location: location
  sku: { name: 'Y1'; tier: 'Dynamic' }
}

// 6. FUNCTION APP (System-Assigned Identity)
resource functionApp 'Microsoft.Web/sites@2022-03-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly:    true
    siteConfig: {
      appSettings: [
        { name: 'AzureWebJobsStorage';  value: storageAccount.properties.primaryEndpoints.blob }
        { name: 'FUNCTIONS_EXTENSION_VERSION'; value: '~4' }
        { name: 'WEBSITE_RUN_FROM_PACKAGE';      value: '1' }
        { name: 'KeyVault__VaultUri';            value: keyVault.properties.vaultUri }
        { name: 'OpenAI__Endpoint';              value: openAi.properties.endpoint }
      ]
    }
  }
  dependsOn: [
    storageAccount
    appServicePlan
  ]
}

// 7. KEY VAULT (Access for Function App)
resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku:      { family: 'A'; name: 'standard' }
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: functionApp.identity.principalId
        permissions: { secrets: [ 'get', 'list' ] }
      }
    ]
    enablePurgeProtection: true
  }
  dependsOn: [
    functionApp
  ]
}

// 8. BOT SERVICE
resource botService 'Microsoft.BotService/botServices@2021-05-01' = {
  name: botServiceName
  location: location
  kind: 'bot'
  sku:  { name: 'F0' }
  properties: {
    displayName: botServiceName
    endpoint:    'https://${functionApp.defaultHostName}/api/messages'
  }
  dependsOn: [
    functionApp
  ]
}

// 9. PRIVATE ENDPOINTS
module peStorage 'modules/privateEndpoint.bicep' = {
  name: 'peStorage'
  params: {
    parentResourceId: storageAccount.id
    endpointName:     'pe-${storageAccount.name}'
    groupIds:         [ 'blob' ]
    subnetId:         peSubnetId
    location:         location
  }
  dependsOn: [
    storageAccount
    vnetModule
  ]
}

module peSearch 'modules/privateEndpoint.bicep' = {
  name: 'peSearch'
  params: {
    parentResourceId: searchService.id
    endpointName:     'pe-${searchService.name}'
    groupIds:         [ 'searchService' ]
    subnetId:         peSubnetId
    location:         location
  }
  dependsOn: [
    searchService
    vnetModule
  ]
}

// 10. PRIVATE DNS ZONES & VNET LINKS
module pdzStorage 'modules/privateDnsZone.bicep' = {
  name: 'pdzStorage'
  params: {
    zoneName: 'privatelink.blob.core.windows.net'
    vnetId:   vnetModule.outputs.vnetId
  }
  dependsOn: [ peStorage ]
}

module pdzSearch 'modules/privateDnsZone.bicep' = {
  name: 'pdzSearch'
  params: {
    zoneName: 'privatelink.search.windows.net'
    vnetId:   vnetModule.outputs.vnetId
  }
  dependsOn: [ peSearch ]
}
