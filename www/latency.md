## Latency prediction

For many players, latency is a very easy way to gauge a server's playability.

Because we can't ping servers through the browser, we have to try and convert distance
between you (or at least what your browser reports) to the server (approximated by GeoIP).

Posted below is sampled data.  First coordinate is distance in KM, second is sampled ping.

linear fit {360,38},{920,59},{2200,82},{12000,220},{9100,187},{8900,179},{3900,105},{8800,165},{1600,55},{3500,108}

= (0.0151429 * distance) + 42.1474