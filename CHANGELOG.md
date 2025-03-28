The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

This project uses [Semantic Versioning](https://semver.org/) - MAJOR.MINOR.PATCH

# Changelog

## 4.4.0 (2025-03-27)


### Added

- Performance improvements for the cloud create calls. [#81](https://github.com/salt-extensions/saltext-azurerm/issues/81)

## 4.3.0 (2025-03-17)


### Added

- Added `public_ip_sku` and `public_ip_allocation_method` fields for cloud profiles. [#72](https://github.com/salt-extensions/saltext-azurerm/issues/72)

## 4.2.0 (2025-03-12)


### Added

- Added `custom_data`, `user_data`, `identity_type` and `user_assigned_identities` fields for cloud profiles. [#68](https://github.com/salt-extensions/saltext-azurerm/issues/68)


## 4.1.1 (2025-03-06)


### Fixed

- Removed restriction of VM sizes to known ones [#56](https://github.com/salt-extensions/saltext-azurerm/issues/56)


## 4.1.0 (2024-04-22)


### Fixed

- Fixed TypeError for ManagedIdentityCredential when using service principal credentials. [#46](https://github.com/salt-extensions/saltext-azurerm/issues/46)


### Added

- Set Virtual Machine Tags via Salt Cloud [#47](https://github.com/salt-extensions/saltext-azurerm/issues/47)


## 4.0.1 (2023-08-14)

### Fixed

- Fix NameError for __salt__ access and a public IP KeyError (#40)


## 4.0.0 (2023-08-14)

### Added

- Added virtual machine and virtual machine extension modules
- Updated cloud module to use execution modules instead of its own workflow

### Fixed

- Fix docs link in README to point to readthedocs (#37)


## 3.0.0 (2023-07-10)

### Added

- Add more ARM compute functionality - VMs, disk, images (#34)
- Port AzureFS backend from Salt (#31)
- Add KeyVault operations (#28)

### Deprecated

- Start to deprecate msrestazure (#32)


## 2.0.2 (2023-02-13)

### Fixed

- Fix deployment resource validation function (#21)


## 2.0.1 (2023-02-13)

### Fixed

- Fix deployment resource functions with use of the new pinned SDK versions (#20)


## 2.0.0 (2022-09-26)

### Added

- Updated all Azure SDK versions to recent releases and updated base code to accommodate changes.


## 1.0.0 (2022-06-21)

### Added

- Initial version of Microsoft Azure Cloud Modules Extension for Salt. This release tracks the functionality in the
  core Salt code base as of version 3005.
