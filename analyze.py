import json
from numpy.lib import pad
import pandas as pd
from scipy.stats import ttest_rel

SIGNIFICANCE_LEVEL = .05

def analyze(df, before, after):
    views = {
        'internal': df[df['referer_class'] == 'internal'].groupby(['continent', 'access_method', 'date']).sum(),
        'external': df[df['referer_class'] == 'external'].groupby(['continent', 'access_method', 'date']).sum()
    } 
    results = {
        'internal': {
            'increase': {'mobile web': [], 'desktop': []},
            'decrease': {'mobile web': [], 'desktop': []},
            'no_difference': {'mobile web': [], 'desktop': []}
        },
        'external': {
            'increase': {'mobile web': [], 'desktop': []},
            'decrease': {'mobile web': [], 'desktop': []},
            'no_difference': {'mobile web': [], 'desktop': []}
        }
    }


    for view, data in views.items():
        for access_method in ('mobile web', 'desktop'):
            for continent in data.index.levels[0]:
                # filter the before and after values
                views_before_change = data[
                        data.index.map(lambda x: x[0] == continent and x[1] == access_method and x[2] <= before)
                    ].values[:, 0]
                views_after_change =  data[
                        data.index.map(lambda x: x[0] == continent and x[1] == access_method and x[2] >= after)
                    ].values[:, 0]

                if not views_before_change.size or not views_after_change.size:
                    continue

                # make the arrays equal size
                number_of_missing_data = views_before_change.size - views_after_change.size
                if number_of_missing_data > 0:
                    views_after_change = pad(
                        views_after_change,
                        [0, number_of_missing_data], 'constant', constant_values=[0]
                    )
                elif number_of_missing_data < 0:
                    views_before_change = pad(
                        views_before_change,
                        [0, abs(number_of_missing_data)], 'constant', constant_values=[0]
                    )

                t_statistic, p_value = ttest_rel(views_before_change, views_after_change)
                mean_views_before_change = views_before_change.mean()
                mean_views_after_change = views_after_change.mean()
                mean_change = (mean_views_after_change - mean_views_before_change) / mean_views_before_change
                mean_change = "%.2f" % round(100 * mean_change, 2) + '%'

                if p_value < SIGNIFICANCE_LEVEL:
                    # reject the null hypothesis of means being equal
                    if t_statistic < 0:
                        results[view]['increase'][access_method].append(continent + ': ' + mean_change)
                    else:
                        results[view]['decrease'][access_method].append(continent + ': ' + mean_change)
                else:
                    results[view]['no_difference'][access_method].append(continent + ': ' + mean_change)
    print(json.dumps(results, indent=True))

if __name__ == '__main__':
    # analyze 2015
    df = pd.read_csv('pageviews_2015.tsv', sep='\t', parse_dates={'date': [1, 2, 3]})
    print('2015')
    analyze(df, pd.to_datetime('2015-08-02'), pd.to_datetime('2015-08-13'))

    # analyze 2014
    df = pd.read_csv('pageviews_2014.tsv', sep='\t', parse_dates={'date': [0]})
    print('2014')
    analyze(df, pd.to_datetime('2014-08-02'), pd.to_datetime('2014-08-13'))

    #analyze 2015 (pageviews for top pages)
    df = pd.read_csv('pageview_top_pages_2015.tsv', sep='\t', parse_dates={'date': [1, 2, 3]})
    print('2015 (top pages)')
    analyze(df, pd.to_datetime('2015-08-02'), pd.to_datetime('2015-08-13'))
