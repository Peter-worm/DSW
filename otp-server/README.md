# OTP-Server (Warsaw)

Minimal, reproducible OpenTripPlanner image for Warsaw.

```
otp-server/
├── Dockerfile     # builds OTP 2.7.0, downloads GTFS, bakes graph
└── warsaw.pbf     # OSM extract (≈ 58 MB) already in repo
```

## Build once

```bash
docker build -t otp-warsaw .
```

## Run

```bash
docker run -p 8080:8080 otp-warsaw
```

OTP starts in seconds and serves the GTFS GraphQL API at
[http://localhost:8080/otp/gtfs/v1](http://localhost:8080/otp/gtfs/v1).

## Updating the feed

```bash
docker build \
  --build-arg GTFS_URL=https://mkuran.pl/gtfs/warsaw.zip \
  -t otp-warsaw .
```

The build stage re-downloads the GTFS zip and rebuilds the graph; runtime
remains unchanged.

