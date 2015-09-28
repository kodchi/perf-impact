A simple script that tests the impact of performance changes to the number of
page views across the globe.

We wanted to know how the performance improvements patch [1] has impacted the
page load times. We hypothesized that the faster load times would lead
to more page views. Thus we took a sample of 41 days before and 41 days
after the patch was deployed and measured the number of page views for each day.
Then we applied a t-test to see whether there was a statistically significant
difference between the average number of page views over 41 days in the
above two samples.

To gain a better insight each continent and access mode (mobile web or desktop)
was looked at separately.

The t-test gave us the following [results](#results).


[1] https://gerrit.wikimedia.org/r/#/c/227627/

## Query
### For the year 2015
the data is taken from wmf.pageview_hourly table by running the following query:
```hiveql
SELECT continent, year, month, day, referer_class, sum(view_count) as view_count, access_method
FROM wmf.pageview_hourly
WHERE
    (
      (CONCAT(year, "-", LPAD(month, 2, "0"), "-", LPAD(day, 2, "0")) BETWEEN "2015-06-23" AND "2015-08-02")
     OR
      (CONCAT(year, "-", LPAD(month, 2, "0"), "-", LPAD(day, 2, "0")) BETWEEN "2015-08-13" AND "2015-09-22")
    )
    AND agent_type = "user"
    AND (access_method = "desktop" OR access_method = "mobile web")
GROUP BY continent, year, month, day, referer_class, access_method;
```

#### For the year 2014
the data is taken from milimetric.webrequest_sampled table by running the following query. The query applies new page view definitions to the old data.
```hiveql
ADD JAR /srv/deployment/analytics/refinery/artifacts/refinery-hive.jar;
CREATE TEMPORARY FUNCTION client_ip as 'org.wikimedia.analytics.refinery.hive.ClientIpUDF';
CREATE TEMPORARY FUNCTION geocoded_data as 'org.wikimedia.analytics.refinery.hive.GeocodedDataUDF';
CREATE TEMPORARY FUNCTION is_pageview as 'org.wikimedia.analytics.refinery.hive.IsPageviewUDF';
CREATE TEMPORARY FUNCTION get_access_method as 'org.wikimedia.analytics.refinery.hive.GetAccessMethodUDF';
CREATE TEMPORARY FUNCTION classify_referer AS 'org.wikimedia.analytics.refinery.hive.RefererClassifierUDF';
CREATE TEMPORARY FUNCTION is_wikimedia_bot as 'org.wikimedia.analytics.refinery.hive.IsWikimediaBotUDF';
CREATE TEMPORARY FUNCTION ua_parser as 'org.wikimedia.analytics.refinery.hive.UAParserUDF';
CREATE TEMPORARY FUNCTION is_spider as 'org.wikimedia.analytics.refinery.hive.IsSpiderUDF';

SELECT 
    SUBSTR(dt, 0, 10) as ymd,
    geocoded_data(client_ip(ip, x_forwarded_for))['continent'] as continent,
    classify_referer(referer) as referer_class,
    COUNT(*) as view_count,
    get_access_method(COALESCE(parse_url(uri, 'HOST'), ""), user_agent) as access_method
FROM milimetric.webrequest_sampled
WHERE
    is_pageview(
        COALESCE(parse_url(uri, 'HOST'), ""),
        COALESCE(parse_url(uri, 'PATH'), ""),
        COALESCE(parse_url(uri, 'QUERY'), ""),
        split(status,'/')[1],
        content_type,
        user_agent
    ) = 1
    AND
    (
      SUBSTR(dt, 0, 10) BETWEEN "2014-06-23" AND "2014-08-02"
     OR
      SUBSTR(dt, 0, 10) BETWEEN "2014-08-13" AND "2014-09-22"
    )
    AND CASE
        WHEN ((is_wikimedia_bot(user_agent))) THEN 'bot'
        WHEN ((ua_parser(user_agent)['device_family'] = 'Spider') OR (is_spider(user_agent))) THEN 'spider'
        ELSE 'user'
    END = 'user'
    AND get_access_method(COALESCE(parse_url(uri, 'HOST'), ""), user_agent) IN ('desktop', 'mobile web')
GROUP BY
    SUBSTR(dt, 0, 10),
    geocoded_data(client_ip(ip, x_forwarded_for))['continent'],
    classify_referer(referer),
    get_access_method(COALESCE(parse_url(uri, 'HOST'), ""), user_agent)
;
```

### 2015, top 1000 pages (removing non-main namespaced pages and pages with problematic titles) on 06/23/2015.
The result of the query will be used to select [the view counts of the top 1000 pages](#for-the-year-2015-when-considering-the-top-pages-only).
```hiveql
SELECT project, page_title, SUM(view_count) as view_count
FROM wmf.pageview_hourly
WHERE
    CONCAT(year, "-", LPAD(month, 2, "0"), "-", LPAD(day, 2, "0")) = "2015-06-23"
    AND agent_type = "user"
    AND (access_method = "desktop" OR access_method = "mobile web")
    AND INSTR(page_title, ":") = 0
    AND INSTR(page_title, "�") = 0
    AND LENGTH(page_title) > 2
GROUP BY project, page_title
ORDER BY view_count DESC
LIMIT 1000;
```

## Results
At 5% significance level, the following changes were statistically significant:

### For the year 2015
```json
{
 "external": {
  "increase": {
   "desktop": [
    "Africa: 7.95%",
    "North America: 16.48%",
    "Oceania: 16.38%",
    "South America: 12.99%"
   ],
   "mobile web": [
    "Africa: 8.16%",
    "Antarctica: inf%",
    "Europe: 7.80%",
    "North America: 5.59%",
    "South America: 6.89%"
   ]
  },
  "decrease": {
   "desktop": [
    "Unknown: -37.10%"
   ],
   "mobile web": [
    "Unknown: -77.07%"
   ]
  },
  "no_difference": {
   "desktop": [
    "Antarctica: 14.29%",
    "Asia: 1.93%",
    "Europe: 8.52%"
   ],
   "mobile web": [
    "Asia: 1.00%",
    "Oceania: 0.87%"
   ]
  }
 },
 "internal": {
  "increase": {
   "desktop": [
    "Oceania: 8.85%"
   ],
   "mobile web": [
    "Africa: 9.40%",
    "Asia: 5.95%",
    "Europe: 7.83%",
    "South America: 5.49%"
   ]
  },
  "decrease": {
   "desktop": [
    "Unknown: -36.09%"
   ],
   "mobile web": [
    "Unknown: -72.84%"
   ]
  },
  "no_difference": {
   "desktop": [
    "Africa: 3.24%",
    "Asia: 1.83%",
    "Europe: 3.53%",
    "North America: 3.62%",
    "South America: 0.20%"
   ],
   "mobile web": [
    "North America: 1.08%",
    "Oceania: 2.87%"
   ]
  }
 }
}
```
### For the year 2014
```json
{
 "internal": {
  "increase": {
   "mobile web": [
    "Africa: 15.94%", 
    "Asia: 18.31%", 
    "Europe: 17.85%", 
    "Unknown: 39.83%"
   ], 
   "desktop": [
    "Africa: 32.04%", 
    "Europe: 37.90%", 
    "North America: 19.16%", 
    "Oceania: 21.51%", 
    "South America: 20.38%"
   ]
  }, 
  "no_difference": {
   "mobile web": [
    "North America: 11.23%", 
    "Oceania: 11.57%", 
    "South America: 12.54%"
   ], 
   "desktop": [
    "Asia: 7.48%", 
    "Unknown: -2.70%"
   ]
  }, 
  "decrease": {
   "mobile web": [], 
   "desktop": []
  }
 }, 
 "external": {
  "increase": {
   "mobile web": [
    "Africa: 27.48%", 
    "Asia: 27.92%", 
    "Europe: 30.58%", 
    "North America: 29.59%", 
    "Oceania: 21.68%", 
    "South America: 33.52%", 
    "Unknown: 81.26%"
   ], 
   "desktop": [
    "Africa: 31.94%", 
    "Asia: 22.62%", 
    "Europe: 27.07%", 
    "North America: 39.19%", 
    "Oceania: 38.73%", 
    "South America: 32.03%"
   ]
  }, 
  "no_difference": {
   "mobile web": [], 
   "desktop": [
    "Unknown: 18.01%"
   ]
  }, 
  "decrease": {
   "mobile web": [], 
   "desktop": []
  }
 }
}
```

### For the year 2015, when considering the top pages only
```hiveql
{
 "internal": {
  "increase": {
   "mobile web": [
    "Africa: 3.94%"
   ], 
   "desktop": []
  }, 
  "no_difference": {
   "mobile web": [], 
   "desktop": [
    "Africa: -3.85%"
   ]
  }, 
  "decrease": {
   "mobile web": [
    "Asia: -14.89%", 
    "Europe: -11.97%", 
    "North America: -27.91%", 
    "Oceania: -23.18%", 
    "South America: -23.51%", 
    "Unknown: -75.93%"
   ], 
   "desktop": [
    "Asia: -18.12%", 
    "Europe: -13.81%", 
    "North America: -14.86%", 
    "Oceania: -14.30%", 
    "South America: -26.85%", 
    "Unknown: -28.22%"
   ]
  }
 }, 
 "external": {
  "increase": {
   "mobile web": [], 
   "desktop": []
  }, 
  "no_difference": {
   "mobile web": [], 
   "desktop": []
  }, 
  "decrease": {
   "mobile web": [
    "Africa: -9.68%", 
    "Asia: -27.78%", 
    "Europe: -20.99%", 
    "North America: -34.29%", 
    "Oceania: -26.39%", 
    "South America: -44.96%", 
    "Unknown: -80.37%"
   ], 
   "desktop": [
    "Africa: -7.80%", 
    "Asia: -22.59%", 
    "Europe: -16.46%", 
    "North America: -26.63%", 
    "Oceania: -15.41%", 
    "South America: -30.40%", 
    "Unknown: -59.15%"
   ]
  }
 }
}
```

## Dependencies
`numpy`, `scipy`, `pandas`

Tested with python 3.4.3.


