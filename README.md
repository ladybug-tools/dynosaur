<img src="https://user-images.githubusercontent.com/2915573/31320448-c5998df4-ac42-11e7-8573-fa0144fb522e.png" width="150" height="150" />

# dynosaur
dynosaur is a package for DynamoBIM to extract geometrical and non-geometrical info from Revit rooms and spaces.

![image](https://user-images.githubusercontent.com/2915573/31094008-98a0bd7e-a781-11e7-8f39-bb5e98ec7585.png)

## name
Dynosaur (not dinosaur) was picked for this package mainly because it tries to address an ancient issue which should not even exist! It also has the `dyn` part in the name which makes it dynamo friendly.

## background
Revit is supposed to be/is a BIM (Building Information Modeling) platform which promises to provide more than just the geometry (e.g. Information). Interestingly enough this information is not always easy to access. One of which is the room/space geometry! In an ideal world (or even a world which is not ideal but people listen to each other!) it should be part of the standard Revit features but it is not! I opened [an idea](https://forums.autodesk.com/t5/revit-ideas/api-access-to-room-openings-geometry-and-materials-in-revit/idi-p/6642406) on 10-24-2016 and collected support to make it happen but it doesn't seem to be considered and implemented any time soon! dynosaur will get this issue sorted out.

## goal
A package to extract geometrical and non-geometrical information from Revit rooms and spaces.

## roadmap
- [x] copy the code available in honeybee's revit.py and put it in a python library structure.
- [x] review current open issues on honeybee repository about extracting room geometry! Anton has also made a number of changes to code after testing a number of rooms.
- [ ] enhance the performance of the code for large models with several rooms.
- [ ] release an alpha version to test the code against users' models and debug. 
- [ ] add non-geometrical data to dynosaur!
- [ ] add support for non-planar surfaces.
- [ ] hopefully by the time Autodesk opens their Room API and we can let dynosaur to happily become extinct!

## contribute
You can contribute by:
1. testing the development and reporting the issues
2. sharing your similar code or scripts
3. forking the repository and contributing code!
