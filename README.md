# Strava stats as a wallpaper

## Prerequsities
```
cd install
sudo apt-get install xfonts-75dpi
sudo dpkg -i ./wkhtmltox_0.12.6.1-2.jammy_amd64.deb
```


new ver
```
{
  "version": 2,
  "builds": [
    {
      "src": "Dockerfile",
      "use": "@vercel/docker"
    }
  ]
}
```

TODO: next 
- convert DB = start_date to a timestamp
- filters on js