.. imap documentation master file, created by
   sphinx-quickstart on Wed Apr 26 18:52:11 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

imap
==================

**imap** is a tool for visualize and convert format of the hd-map. This
project was inspired by Apollo.

.. figure:: /_static/example.png
   :alt: example


**Supported features**:

-  Visualize the hd-map, supported formats: Apollo, OpenDrive.
-  Convert format: Opendrive to Apollo format.
-  Find lane by id

======= ========================= ======
os      support                   remark
======= ========================= ======
ubuntu  yes
mac     yes
windows yes
======= ========================= ======

.. toctree::
   :caption: Contents:
   :numbered: 3
   :maxdepth: 4
   :hidden:

Related work
==================

-  `odrviewer.io <https://odrviewer.io/>`__ is an excellent interactive
   online OpenDRIVE viewer.
-  `esmini <https://github.com/esmini/esmini>`__ is a basic OpenSCENARIO
   player.
-  `apollo_map <https://github.com/Flycars/apollo_map>`__ convert carla
   map to apollo

Quick start
==================

Install
^^^^^^^

You can install imap by following cmd.

.. code:: shell

   pip3 install imap_box

Example
==================

1. Visualization
^^^^^^^^^^^^^^^^

After the installation is complete, you can view the map with the
following command.

.. code:: shell

   imap -m data/borregas_ave.txt
   // or
   imap -m data/town.xodr

Currently supported formats:
-  Apollo map
-  OpenDrive map

2. Find lane by id
^^^^^^^^^^^^^^^^^^

You can use below command to find lane by id, Found lane is shown in
**Red**.

.. code:: shell

   imap -m data/borregas_ave.txt -l lane_35

3. Format conversion
^^^^^^^^^^^^^^^^^^^^

Now you can convert OpenDrive map to Apollo map by following command.

.. code:: shell

   imap -f -i data/town.xodr -o data/apollo_map.txt

The following is the display of the hd-map in
``data\borregas_ave.txt``.You can click on the lane you want to display
more detail info, which will display the current lane’s id, as well as
the predecessor and successor lane’s id in the upper left corner.

.. figure:: /_static/map_show.jpg
   :alt: map_show


Questions
==================

Q: After running the command ``imap -m data/your_map_file``, nothing display and no errors!!!

A: Check the permissions of the map file, if the current user does not have
permissions, modify the permissions with the following commands.

.. code:: shell

   sudo chmod 777 data/your_map_file



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
