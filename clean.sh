# delete plots results
find "pysrc/metric_plots" -type f -print -delete

# delete calculated weights except anything under pysrc/models/teacher/
find "pysrc/models" -type f ! -path "pysrc/models/teacher/*" -print -delete
