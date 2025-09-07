# Backup and Restore Guide

This guide outlines the procedures for backing up and restoring the system's data.

## 1. Backing Up Data

The following data should be backed up regularly:

* **Qdrant Vector Database:** The Qdrant documentation provides instructions for backing up and restoring the database.
* **Configuration Files:** The `.env` and `mkdocs.yml` files should be backed up.
* **Knowledge Base:** The `knowledge` directory should be backed up.

## 2. Restoring Data

To restore the system's data, follow these steps:

1. **Restore the Qdrant database:** Follow the instructions in the Qdrant documentation to restore the database from a backup.
2. **Restore the configuration files:** Restore the `.env` and `mkdocs.yml` files from a backup.
3. **Restore the knowledge base:** Restore the `knowledge` directory from a backup.
