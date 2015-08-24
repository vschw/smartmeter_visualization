# smartmeter_visualization
Data (csv) download and visualization tool for smartmeter

## Examples

```shell
python smvi.py -n=999
```

![figure_1](https://cloud.githubusercontent.com/assets/11513117/9438141/54e11578-49f7-11e5-8088-841c35dfce3c.png)

```shell
python smvi.py -n=999 -s=2015-08-19 -e=2015-08-20 -x=13:20:00 -y=14:20:00 -c=1 -a=false
```

![figure_2](https://cloud.githubusercontent.com/assets/11513117/9438282/5abb163c-49f8-11e5-88d0-81f53b736e66.png)


## Dependencies

[paramiko_scp](https://github.com/jbardin/scp.py)

## Optional arguments

argument | short | long | description | default | required 
--- | --- | --- | --- | --- | ---
   | -h | --help | show this help message and exit | | false
NODES | -n | --nodes |  single node as int, aggregate of multiple nodes as comma-separated list (e.g.: 1,2,3,4) | | true
TIMEZONE | -t | --timezone | timezone as int from -12 to 12 in relation to UTC time (e.g.: -8) | 0 | false
STARTDATE | -s | --startdate | start date - format YYYY-MM-DD | <two days ago> | false
ENDDATE | -e | --enddate | end date - format YYYY-MM-DD | <yesterday> | false
STARTTIME | -x | --starttime | start time - format HH:MM:SS | 00:00:00 | false
ENDTIME | -y | --endtime | end time - format HH:MM:SS | 00:00:00 | false
CIRCUIT | -c | --circuit | single circuit as int (1 or 2) | 0 | false
ENERGY | -a | --energy | display energy aggregate in figure (true or false) | true | false
