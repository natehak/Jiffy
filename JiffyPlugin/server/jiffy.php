<?php

  # Get the post variables
  $youtube = $_POST["youtube"];
  $start = $_POST["start"];
  $stop = $_POST["stop"];

  $path = "/full/path/to/folder/where/python/script/is/in/";

  $link = escapeshellcmd(exec($path . "bin/python " . $path . "togif.py " . $youtube . " " . $start . " " . $stop));

  $file = "/full/path/to/where/gif/links/should/be/logged.log";
  file_put_contents($file, $link . "\n", FILE_APPEND);

  echo($link);

?>
