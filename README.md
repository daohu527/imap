# imap

[![Documentation Status](https://readthedocs.org/projects/imap/badge/?version=latest)](https://imap.readthedocs.io/en/latest/?badge=latest)

**[imap](https://imap.readthedocs.io/en/latest/)** is a tool for visualize and convert format of the hd-map. This project was inspired by Apollo.

![example](docs/_static/example.png)

**Supported features**:
1. Visualize the hd-map, supported formats: Apollo, OpenDrive.
2. Find lane by id
3. Convert format: Opendrive to Apollo format.

| os      | support                 | remark |
|---------|-------------------------|--------|
| ubuntu  | :heavy_check_mark:      |        |
| mac     | :heavy_check_mark:      |        |
| windows | :heavy_check_mark:      |        |

## Related work
- [odrviewer.io](https://odrviewer.io/) is an excellent interactive online OpenDRIVE viewer.
- [esmini](https://github.com/esmini/esmini) is a basic OpenSCENARIO player.
- [apollo_map](https://github.com/Flycars/apollo_map) convert carla map to apollo

## Quick start

#### Install
You can install imap by following cmd.
```shell
pip3 install imap_box
```

## Example
#### 1. Visualization
After the installation is complete, you can view the map with the following command.
```shell
imap -m data/borregas_ave.txt
// or
imap -m data/town.xodr
```
Currently supported formats:
* Apollo map
* OpenDrive map

#### 2. Find lane by id
You can use below command to find lane by id, Found lane is shown in **Red**.
```shell
imap -m data/borregas_ave.txt -l lane_35
```

#### 3. Format conversion
Now you can convert OpenDrive map to Apollo map by following command.
```shell
imap -f -i data/town.xodr -o data/apollo_map.txt
```

The following is the display of the hd-map in `data\borregas_ave.txt`.You can click on the lane you want to display more detail info, which will display the current lane's id, as well as the predecessor and successor lane's id in the upper left corner.

![map_show](docs/_static/map_show.jpg)


## Questions
1. After running the command `imap -m data/your_map_file`, nothing display and no errors!!!

A: Check the permissions of the map file, if the current user does not have permissions, modify the permissions with the following commands.
```shell
sudo chmod 777 data/your_map_file
```
2. Map data permission checking has no problem, still nothing display and no errors!
A: It's better to install imap_box by running "sudo pip3 install imap_box", then run "imap -m xxx.txt".
