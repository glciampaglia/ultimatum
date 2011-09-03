
========================================================
Ultimatum Game Web Application
========================================================
------------------------
Administration and Usage
------------------------

:Author: Giovanni Luca Ciampaglia <ciampagg@ethz.ch>
:Copyright: This code is © copyright of ETH Zürich 2010.

.. contents::

1. Requirements
---------------

The following software is needed to run the web application for ultimatum game
experiments:

* python 2.4+   (http://www.python.org)
* Django 1.2    (http://www.djangoproject.com)
* GNU gettext   (http://www.gnu.org)
* htmldoc       (http://www.htmldoc.org)
* NumPy         (http://www.numpy.org)

Apache (http://www.apache.org) and MySQL (http://www.mysql.org) are additionally
needed for deploying the web application on a real web server.  All these
requirements are already met for our web instance [Hermes]_.

If you want to run the web app locally on your machine without using Apache (see
§2.1), the following is needed instead of MySQL:

* SQLite        (http://www.sqlite.org)

You can quickly test if SQLite is installed on your machine by opening a
terminal and typing:

::

    $ sqlite3

2. Installation and deployment
------------------------------

To install the application simply extract the archive somewhere (for example
in your home folder):

::

    $ tar xvfz ultimatum-0.2.tar.gz 

The next steps depend on whether you want to run the web app locally on your
machine (§ 2.1) or you want to deploy it on a server (§ 2.2). The first case is
ideal for testing and developing. Experiments with real participants, on the
other hand, should be performed only with the latter setup.


2.1 Testing it works
~~~~~~~~~~~~~~~~~~~~

The web framework Django has built-in a small web server for serving static
files, and is all you need to test whether the web app works [#]_. First, open
the file **urls.py** and check that the following line is *uncommented*:

::

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root' : abspath('./static/')}),

then make sure that **manage.py** has executable permissions:

:: 

    $ chmod u+x manage.py

and run it:

::

    $ ./manage.py runserver

you should get something like this:

::

    Validating models...
    0 errors found

    Django version 1.2.3, using settings 'ultimatum.settings'
    Development server is running at http://127.0.0.1:8000/
    Quit the server with CONTROL-C.

Now point your browser to http://127.0.0.1:8000/experiment and the experiment
page should be displayed. In case of errors, you should get a page that shows a
traceback of the error. Note that if you just point to the URL displayed in the
console, you will see an error page. This is because the home page is
currently not used. This is also the case on the hermes instance, only that
instead of the traceback information, you get a "404 Not Found" page. 

Note that in this case data are stored in a SQLite DB situated in the file
**empty.db**.

2.2 Deployment with Apache
~~~~~~~~~~~~~~~~~~~~~~~~~~

There are several methods available for deploying a Django web app [#]_, and the
recommended one is to use Apache and mod_wsgi, which is the one we use here. In
order to tell Apache how to run the web app, a few configuration options must be
prepared, telling where to locate the Python code of the web app, etc. These
options go in a file called **apache/django.wsgi**.  What this file does is
simply to append a few locations to the PYTHONPATH (a variable that tells the
Python interpreter where to look when locating modules) and to add the location
of the file **settings.py** to the Unix environment, in a variable called
DJANGO_SETTINGS_MODULE. 

Currently the web application is deployed on our web server instance [Hermes]_,
so the file contains already settings relative to this machine. On the side of
Apache, its configuration file [#]_, which is not included in the source
archive, needs the following information (again, settings that make sense for
[Hermes]_):

::

    ### ---------- Django configuration with mod_wsgi ----------------- ###

    # Directory from where to serve static content

    Alias /media/ /instances/home/hermes/htdocs/media/

    Alias /static/ /instances/home/hermes/ultimatum/static/

    <Directory "/instances/home/hermes/ultimatum/static">
            AllowOverride
            Options None
            Order allow,deny
            Allow from all
    </Directory>

    # WSGI server script

    WSGIScriptAlias / /instances/home/hermes/ultimatum/apache/django.wsgi

    <Directory /instances/home/hermes/ultimatum/apache>
    Order deny,allow
    Allow from all
    </Directory>

    # Expiration settings
    ExpiresActive on
    ExpiresByType image/jpg "access plus 2 hours"
    ExpiresByType image/png "access plus 2 hours"
    ExpiresByType text/css "access plus 2 hours"

The first two aliases tell Apache were static and media files are located. The
first one, `/media/`, is needed by the Django admin interface application (see
below). On Hermes its contents have already been imported from the Django source
tree. The second one, `/static/`, is instead the location for *our* static
files (like stylesheets). Apart from static content, the WSGI web app is responsible for serving
anything else via the `WSGIScriptAlias` directive. Finally expiration settings
are set for image files (we use only JPG and PNG files) and CSS files.  This
last setting is greatly needed to reduce the bandwith of the server: in this way
web clients will request files of those kinds only once every two hours, instead
of requesting them every time a page is loaded. Finally, open the file
**urls.py** and check that the following line is *commented*:

::

    # (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root' : abspath('./static/')}),

The final step is the setup of the MySQL database. Database settings (type of
DBMS, host name of the DB server, user name and password) must be provided in
the file **settings.py**. By default, the values there let you use a SQLite DB
contained in the file **empty.db**. Hermes has been instead configured to
connect to a separate MySQL server.

For a fresh install, you should thus edit these settings and use the
script **manage.py** to actually create the database tables [#]_.

Now you just have to (re)start Apache (see below for instructions on how to so)
and point your browser to the web app URL, e.g.:
http://www.hermes.ethz.ch/experiment/.

2.3 Hermes Web Instance Administration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Our web server [Hermes]_ runs as an `instance` on a machine called Grandwazoo
[#]_. This is nothing more than a way to say that you have a bunch of processes
running on Grandwazoo under a specific user (in our case **w3_hermes**) that you
can start or stop without affecting other instances. These processes
are the Apache web server (httpd) and the Samba daemons (smbd and nmbd). You can
access Hermes by:

- Samba (Windows shares): point your browser to \\\\www.hermes.ethz.ch\\. Use
  your ETH login to access.

- WebDAV, using your ETH login. With SSL enabled, WebDAV is reachable via
  https://www.hermes.ethz.ch/webdav. Note that, for security reasons, it is not
  a good idea to access WebDAV without SSL!

- SSH/SCP, SSH access is allowed by public key only. Generate a ssh public key
  with ssh-keygen and upload it (via Samba for example) to

  ::

    ~/.ssh/authorized_keys. 
    
  When your public key is installed, you can ssh to the machine using 
  
  ::
  
    ssh w3_hermes@www.hermes.ethz.ch

Note that all methods require that you are an administrator (mail Cristian Tuduce
<cristian.tuduce@id.ethz.ch> or ask Stefano about that).  Once access has been
setup, the instance can be managed in two ways: via the [WebControl]_ interface
or with command-line tools via SSH.   

So let's see how administration works. To access the web control interface you
need to authenticate with your nethz username and password. Once you are there,
you can stop and restart the instance with just one click. This interface is
easy and intuitive but is also a bit slow at loading.

The other way is a quicker: you can use the commands `stop`, `start` and
`restart` and `status` directly from the SSH shell. Note that whenever you
modify the Python code of the web app, you have to restart the instance to get
it to reload the Python modules.

3. Administration
-----------------

In order to run an experiment, you have to create an experimental session and
define various parameters. The web app has an administrative interface at the
following address:

::

    http://www.hermes.ethz.ch/admin 

or 

::
    
    http://localhost:8000/admin

if you are running the web app locally on your machine. You will be asked a
username and a password to access the admin interface. For the local
installation the default username is **admin** and the password is **admin**. 

For [Hermes]_, this information is provided in a separate file, not contained in
this source code distribution, which you should already have obtained. 

The administrative interface is pretty straight-forward and should not be a
problem to use.


4. Data extraction
------------------

Once you have performed an experimental session, you may want to extract data
for further analysis (for example with R or SPSS).  The first thing to know is
that each experimental session is denoted in the database by a numerical ID. The
administrative interface (see above) provides a summary of all experimental
sessions so you can get the ID of the session you are interested in there. Two
SQL files are provided to extract data about an experimental session.  What is
needed is only that you modify them and insert the ID of the session you want.
The files are **sql/games.sql** and **sql/proposals.sql**. They should be run
directly from the command line, like so:

::
    
    $ mysql -u <username> -p experiment < sql/games.sql > games.txt

They are tested under MySQL but should work fine also with SQLite. 

Notes
-----

.. [#] See here: http://docs.djangoproject.com/en/1.2/howto/static-files/
.. [#] See here: http://docs.djangoproject.com/en/1.2/howto/deployment/
.. [#] On hermes this file is /home/instances/hermes/conf/httpd.conf
.. [#] See the Django tutorial here: http://docs.djangoproject.com/en/1.2/intro/tutorial01/#database-setup
.. [#] This machine is managed by ETHZ ID. Its hostname is grandwazoo.ethz.ch


References
----------

.. [Hermes] http://www.hermes.ethz.ch
.. [WebControl] https://setup2.ethz.ch/webcontrol/index.pl?server=grandwazoo&instance=hermes&name=hermes
