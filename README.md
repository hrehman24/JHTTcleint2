# PWP_JHHT Client

## Overview

This Streamlit client consumes:

- Core Beatify API: `https://jhtt-api.onrender.com/Beatify/api/v1`
- Auxiliary service API: `https://jhttclient.onrender.com/`

The UI is organized into three navigation areas:

- **Main**: Dashboard and analytics visualizations
- **Core**: CRUD workflows for Artists, Albums, Tracks, Users, Playlists
- **Aux**: Auxiliary service overview, summary, top artists, recommendations

## Install and Run

From project root:

```bash
cd API_Client_Auxiliary_service/PWP_JHHT_CLIENT
pip install -r requirements.txt
streamlit run app.py
```

## Docker

Run with compose from the parent folder:

```bash
cd API_Client_Auxiliary_service
cp .env.example .env
docker compose up -d --build
```

Client URL:

- `http://localhost:8501`

## Client Communication Diagram (Complete)

The following vertical communication diagram covers all client use cases.

```mermaid
sequenceDiagram
	actor U as User
	participant C as Client
	participant B as Beatify API
	participant A as Aux API

	U->>C: Set core URL
	U->>C: Set aux URL

	U->>C: Open Main
	C->>A: GET /analytics/summary
	A-->>C: summary
	C->>A: GET /analytics/top-artists
	A-->>C: top artists
	U->>C: View charts

	U->>C: Open Core
	U->>C: List items
	C->>B: GET /{resource}
	B-->>C: list
	U->>C: Get by id
	C->>B: GET /{resource}/{id}
	B-->>C: item
	U->>C: Create
	C->>B: POST /{resource}
	B-->>C: created
	U->>C: Update
	C->>B: PUT /{resource}/{id}
	B-->>C: updated
	U->>C: Delete
	C->>B: DELETE /{resource}/{id}
	B-->>C: deleted

	U->>C: Open Aux
	C->>A: GET /
	A-->>C: info
	C->>A: GET /analytics/summary
	A-->>C: metrics
	C->>A: GET /analytics/top-artists
	A-->>C: ranking
	C->>A: GET /recommendations/user/{id}
	A-->>C: recommendations
```

## Features Checklist

- Configurable core and auxiliary base URLs
- Dashboard cards and charts
- Core resource list/read/create/update/delete flows
- Auxiliary analytics and recommendation views
- Table-oriented data presentation

## Auxiliary Service Run Command

Run in a separate terminal:

```bash
cd API_Client_Auxiliary_service/auxiliary_service
pip install -r requirements.txt
python service.py
```

## Linting

```bash
cd API_Client_Auxiliary_service/PWP_JHHT_CLIENT
pylint app.py api_client.py --rcfile=../.pylintrc --reports=y
```

## Sources

- Streamlit docs: https://docs.streamlit.io/
- Requests docs: https://requests.readthedocs.io/
