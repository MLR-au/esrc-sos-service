<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="eScholarship Research Centre Single Sign on Service">
    <meta name="author" content="Dr Marco La Rosa <m@lr.id.au>">

    <meta http-equiv="cache-control" content="max-age=0" />
    <meta http-equiv="cache-control" content="no-cache" />
    <meta http-equiv="expires" content="0" />
    <meta http-equiv="expires" content="Tue, 01 Jan 1980 1:00:00 GMT" />
    <meta http-equiv="pragma" content="no-cache" />

    <link rel="shortcut icon" href="${request.static_url('essos:static/pyramid-16x16.png')}">

    <title>ESSOS - profile</title>

    <!-- Bootstrap core CSS -->
    <link href="/static/bootstrap.min.css" rel="stylesheet">

  </head>

  <body>
    <div class="container">
        <div class="row">
            <div class="col-sm-12 col-md-12 col-lg-12 text-center">
                <h3><a href="http://www.esrc.unimelb.edu.au" target="_blank">eScholarship Research Centre - Single Sign on Service</a></h3>
            </div>
        </div>
        <div class="row">
            <div class="col-sm-7 col-md-7 col-lg-7">
            </div>
            <div class="col-sm-5 col-md-5 col-lg-5">
                <span class="pull-right">
                    Logged in as: ${fullname} <a href="/logout">(logout)</a>
                </span>
            </div>
        </div>
        <hr/>
        %for app in apps:
            <div class="row well">
                <div class="col-sm-12 col-md-12 col-lg-12">
                   <a href="${app.url}">${app.name}</a>
                </div>
                <div class="col-sm-12 col-md-12 col-lg-12">
                   ${app.description}
                </div>
            </div>
        %endfor
    </div>
  </body>
</html>
