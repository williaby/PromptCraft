@description('Resource ID of the parent service (e.g., storageAccount.id)')
param parentResourceId string

@description('Name to assign to this Private Endpoint')
param endpointName string

@description('Array of group IDs for the private link connection')
param groupIds array

@description('Subnet ID in which to deploy the endpoint')
param subnetId string

@description('Location for all resources')
param location string = resourceGroup().location

resource pe 'Microsoft.Network/privateEndpoints@2021-05-01' = {
  name: endpointName
  location: location
  properties: {
    subnet: {
      id: subnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${endpointName}-pls'
        properties: {
          privateLinkServiceId: parentResourceId
          groupIds: groupIds
        }
      }
    ]
  }
}

output privateEndpointId string = pe.id
