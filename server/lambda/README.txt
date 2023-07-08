Use a Lambda layer

You can create a Lambda layer that includes the 'requests' module. Here are the general steps to do this:

When you are creating a layer for a Python AWS Lambda function, the structure should look like this inside your .zip file:

python/lib/python3.8/site-packages/

So, your package should be inside the site-packages directory. This is how AWS Lambda would expect to see the package files for Python.

On your local machine, create a new directory, and install the 'requests' package to that directory with pip:

here's the script to do this:
-------------------------------
mkdir -p python/lib/python3.10/site-packages
pip install requests -t python/lib/python3.10/site-packages/
zip -r requests_layer.zip python
-------------------------------
These commands first create the necessary directory structure, then install the 'requests' library into the site-packages folder inside that structure, and finally zip up the 'python' directory to create the zip file to upload to AWS Lambda as a layer.

Keep in mind to replace python3.10 with your exact python version if it's different.


Then, Zip the 'python' directory:
-------------------------------



/1 Upload this zip file as a new layer in the AWS Lambda console.
/2 Attach the layer to your Lambda function.
