# Code Styling Rules
## Naming Schemes
### Constants & Enumerations
Constants and Enums should be all uppercase.
OBS: The Enum class should follow the Classes naming scheme
- Examples: DaemonCommandType.CMD_START 
### Variables
Variables should be name with lowercase, descriptive names, with underscore(_) in place of spaces, but not too long(obvious abbreviations are welcome).
Please do not append the type(when applicable) initial to the name like iMyInteger, bBooleanVariable, etc...
- Examples: db, app, endpoints.
### Classes
Classes should be named with the first character uppercase, in this instance camel casing is allowed.
- Examples: User, Endpoint,DaemonCommandType
### Functions
Functions should be all lowercase with underscore(_) in place of spaces.
Function parameters should follow the variable naming scheme.
- Examples: write_endpoint_peer()
## Formatting
All python source files should be formatted with black formatter.
# Project Structure
### Blueprint Structures (webapp)
All blueprint modules should have its `__main__` name on the directory.
Routes should be in routes.py, auxiliary functions on utils.py, forms on forms.py
### Common modules
Common modules(that lives is used in two or more parts of the project) should be put on the common subdirectory and included from there.
and the name of the py file should roughly indicate what it contains, like types.py having the custom classes and enums.
### HTML
All html should live within the webapp/wfadmin/templates and should contain the necessary jinja2 stuff, comments are welcome but not mandatory.
### Other static files(css,javascript,images)
They should live on webapp/wfadmin/static, beware that this directory should be aliased as /static on your nginx or apache configuration!
