# Configuration

JobRadar keeps search preferences outside application code. The public repository can therefore remain generic while each user maintains private local settings.

## Configuration files

- `config/profile.yaml` — candidate profile, skills, preferred role families and eligibility constraints
- `config/locations.yaml` — target countries, cities, optional country aliases, language metadata and remote-search policy
- `config/companies.yaml` — optional Lever, Greenhouse and SmartRecruiters company watchlists
- `config/sources.yaml` — enabled collectors and source-specific search terms

The committed files are examples, not prescribed search settings.

## Keep personal settings private

Create a private local directory:

```powershell
New-Item -ItemType Directory config.local -Force
Copy-Item config\*.yaml config.local\
```

Then put this in `.env`:

```text
CONFIG_DIR_HOST=./config.local
```

`config.local/` is ignored by Git. Docker Compose mounts that directory into the backend as `/app/config`.

The same pattern is available for locally labelled evaluation data:

```powershell
New-Item -ItemType Directory data.local\evaluation -Force
Copy-Item data\evaluation\* data.local\evaluation\
```

and in `.env`:

```text
DATA_DIR_HOST=./data.local
```

## Apply changes

Restart the backend after changing configuration:

```powershell
docker compose restart backend
```
