"""
Application layer package enclosing use cases, boundary ports, and DTOs.

Purpose
-------
Orchestrates the flow of data to and from domain entities. Implements specific
application business workflows and defines abstract boundary ports for external
infrastructure adapters via dependency inversion.

Allowed File Types
------------------
- Application use case interactor modules executing application operations.
- Abstract boundary ports (interfaces/protocols) for persistence and gateways.
- Data Transfer Objects (DTOs) for application boundary inputs and outputs.
"""
