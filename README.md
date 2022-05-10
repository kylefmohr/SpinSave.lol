# SpinSave.lol
A WIP web application to help you visualize your Spin Rhythm save file

If you'd like to run/host this yourself, make sure Python is installed, clone this project, and install the depenedencies with `pip3 install -r requirements.txt`. Then, just run app.py and it should be accessible at http://127.0.0.1:80

TODO:
- [ ] Fix current bar graph
  - [ ] add title
  - [ ] axis labels
  - [x] ensure song titles don't get cut off
- [ ] Add more stats! Radio checkbox to choose before upload?
  - [ ] Best accuracy per song
  - [ ] Highest streak per song
  - [ ] Best score per song
- [ ] Add support for custom songs
  - [ ] Need to find a way to translate what they're called in the save file (example: CUSTOM_spinshare_5e9ba991a546f_975788447) to the actual title
  - [ ] Note to self: spinsha.re api allows looking up [via fileReference, which is formatted as "spinshare_\<hex string>"](https://spinsha.re/api/docs/open/songs#detail)
- [x] Add support for difficulties other than 'XD'
