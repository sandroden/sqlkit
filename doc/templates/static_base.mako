<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        ${metatags and metatags or ''}
        <title>${capture(next.show_title)|util.striptags} &mdash; ${docstitle|h}</title>
        ${next.headers()}
    </head>
    <body>
        ${next.body()}
    </body>
</html>

##<%def name="body()"></%def>

<%!
    local_script_files = []
%>

