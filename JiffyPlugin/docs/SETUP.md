# Setup the server
## Requisites
* [Python 3](http://www.python.org/download/)
* requests (available via pip)
* The latest version of praw (available via pip)
	* Alternatively use [my fork of praw](https://github.com/drkabob/praw)
* youtube-dl (available via pip)
* [ffmpeg](http://www.ffmpeg.org/download.html)
* [gifsicle](http://www.lcdf.org/gifsicle/)
* virtualenv (available via pip)
* A web server that supports PHP scripts (an easy way to setup a LAMP stack Ubuntu is [here](https://help.ubuntu.com/community/ApacheMySQLPHP))
 
## Download
You can either [download a ZIP](https://github.com/drkabob/Jiffy/archive/master.zip) from the GitHub repo or do `git clone https://github.com/drkabob/Jiffy.git`

## Setup
Place `jiffy.php` somewhere that your LAMP server can host it.

## Configuration
First, copy the file `jiffy-sample.cfg` to `jiffy.cfg`. You can use the command `cp jiffy-sample.cfg jiffy.cfg`.

Then follow the directions within the config to setup the new bot.

After that you are going to need to edit some variables inside `jiffy.php`.

Change the `$path` variable to the same thing you set the `path` configuration option to in `jiffy.cfg`. Then change the `$file` variable into where you want Jiffy to log the GIFs it has created. Furthermore, make sure that the PHP process has permissions to write to that file.

Finally, setup a virtualenv with all the required libraries where the python script is located. Make sure its using the Python 3 interpreter.

## Running
Assuming everything is setup correctly, just make a POST request to the PHP script's URL.

It takes all its queries in `x-www-form-urlencoded` format.

The query variables are:
* youtube - A link to the YouTube video you want to turn into a GIF
* start - The timestamp of when you want the GIF to start in YouTube video in X:XX format
* stop - The timestamp of when you want the GIF to stop in YouTube video in X:XX format

# Setup the plugin
The Chrome extension is actually just a Userscript slipstreamed into a Chrome extension. The icon, manifest, and Javascript data is all there so you shouldn't have too much issue. If you are having trouble, just check out [this tutorial](developer.chrome.com/extensions/getstarted.html). Finally, if you want the plugin to generate GIFs from a server that is not mine, just change the URL in the `handleSubmit()` function.


**You're done!**
