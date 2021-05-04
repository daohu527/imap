## imap
Imap tool is used to visualize the hd-map. This project refers to apollo.
```
data     // hdmap dir
main.py  // main process
map.py  // hd-map struct
editor.py  // user interaction
```

## quick start
Install conda first, then install protobuf, use `conda install protobuf` to install will fail, I haven't found the reason yet. Replace with the following command will work.
```
pip install protobuf
```

run the command below.
```
python main.py -m data/borregas_ave.txt
```

## example
The following is the display of the hdmap in `data\borregas_ave.txt`.
![map_show](doc/img/map_show.jpg)  


## todo
1. add argparse.ArgumentParser
2. show map in more details (like layers, styles)  // now
3. select lane to convert color
