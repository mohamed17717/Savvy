cat celery_orm_worker.log | grep "succeeded" | awk '{ print $7, $10 }' | sed 's/..$//' | sed 's/^App.tasks.//' | sed 's/\[[0-9a-f\-]*\]//' | awk '
BEGIN {
    printf "%-35s %-10s %-10s %-10s %-10s %-10s\n", "Method Name", "Max Time", "Min Time", "Avg Time", "Total Time", "Count";
}
{
    count[$1]++; 
    sum[$1] += $2; 
    if(min[$1] == "" || $2 < min[$1]) min[$1] = $2; 
    if(max[$1] == "" || $2 > max[$1]) max[$1] = $2;
}
END {
    for (method in sum) {
        printf "%-35s %10.2f %10.2f %10.2f %10.2f %10d\n", method, max[method], min[method], sum[method] / count[method], sum[method], count[method];
    }
}'
