# ICDMAI Bengaluru Planner

A single-page trip planner for international speakers at ICDMAI 2027 (15–17 January 2027, Christ University, Central Campus, Hosur Road, Bengaluru).

Speakers enter their dates, hotel area and interests and get a day-by-day plan around the conference days, with a cab-time estimate for every ride at the hour they will travel. It also covers places to see, dining and nightlife, where to stay, weather and licensed guides.

## Run it

It is plain HTML, CSS and JavaScript with no build step. Open `index.html` in a browser, or publish the repository root with GitHub Pages.

## How the travel times work

Cab times are estimated, not live. `travel()` in `index.html` takes the straight-line distance, scales it to road distance, and divides by a typical speed for that hour and day type (weekday or weekend). Every ride has a "Live route" link to Google Maps for real-time traffic.

## Photos

Photos come from Wikimedia Commons under free licences. Each photo is credited on the page ("Photo credits" in the footer) with its author and licence. `tools/fetch_images.py` finds and downloads freely licensed photos and records their credits.

## Before the conference

Opening hours, closed days, restaurant and bar details and guide contacts are from public sources and local knowledge. Confirm them before sending the page to speakers.
