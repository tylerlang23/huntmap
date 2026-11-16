# Hunt Map

A personal hunting map for Minnesota: public land, parcel lines with owner names, wind, waypoints, tracks and scouting hot spots.

- `index.html` is the whole app.
- `.github/workflows/build.yml` builds the parcel tile file (`parcels.pmtiles`) from public data and publishes the site with GitHub Pages. It runs on every change and once a month.
- `scripts/counties.txt` lists extra counties to add on top of the state's open parcel dataset.

Boundaries are approximate, not a survey.
