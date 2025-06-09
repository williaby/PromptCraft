@description('Name of the Virtual Network')
param vnetName string

@description('Location for all resources')
param location string = resourceGroup().location

@description('Name of the default subnet')
param defaultSubnetName string = 'default'

@description('CIDR for the default subnet')
param defaultSubnetPrefix string = '10.0.0.0/24'

@description('Name of the private-endpoints subnet')
param peSubnetName string = 'private-endpoints'

@description('CIDR for the private-endpoints subnet')
param peSubnetPrefix string = '10.0.1.0/24'

resource vnet 'Microsoft.Network/virtualNetworks@2021-05-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.0.0.0/16'
      ]
    }
    subnets: [
      {
        name: defaultSubnetName
        properties: {
          addressPrefix: defaultSubnetPrefix
        }
      }
      {
        name: peSubnetName
        properties: {
          addressPrefix: peSubnetPrefix
        }
      }
    ]
  }
}

output vnetId string           = vnet.id
output defaultSubnetId string = vnet.properties.subnets[0].id
output peSubnetId string      = vnet.properties.subnets[1].id
