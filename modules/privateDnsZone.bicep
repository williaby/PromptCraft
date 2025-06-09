@description('Name of the Private DNS zone (e.g., privatelink.blob.core.windows.net)')
param zoneName string

@description('ID of the VNet to link (output from vnet module)')
param vnetId string

@description('Location for DNS zones is always "global"')
var location = 'global'

resource dnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: zoneName
  location: location
}

resource vnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  name: '${zoneName}/link-${uniqueString(vnetId)}'
  properties: {
    virtualNetwork: {
      id: vnetId
    }
    registrationEnabled: false
  }
  dependsOn: [
    dnsZone
  ]
}

output dnsZoneId string = dnsZone.id
output vnetLinkId string  = vnetLink.id
