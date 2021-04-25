# py-tpm-analysis

A python script that takes a folder of analytical data from either `tpm2-algtest`, Windows' `tpmtool` (gatherlogs) 
command or `tpm2-tools`'s `tpm2-getcap` command and processes this date to a human-readable form as a simple web application.

## How to run it:
e.g. `./results --output=./output -d=True`

- first argument is the source folder; results are in form of:
    - `.txt` file - for `tmptool` output (either in a folder or in the root)
    - in a folder with `tpm2-getcap` files (i.e. quicktest algorithms, commands, ecc-curves, properties-fixed). 
      Naming must be the identical to the one created by `tpm2-algtest`.
    - in a folder with `tpm2-algtest`'s results in either revision state
    - either of those above in a `.zip` file
- the `output` parameter sets the desired data output folder
- the `d` parameter decides if duplicates should be ignored should any happen when unzipping zipped files (use with `true` if
  you run it for the first time)
  
# Output

The output is a simple web application. The element with a class `tpm-data` in `index.html` can be embedded in a website 
should all other files be transferred as well in the same directory structure as outputted.

### Important note

The web app only runs on a web server in order to fetch the needed `.json` files - either local or remote.