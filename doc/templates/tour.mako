## coding: utf-8
<%inherit file="layout.mako"/>

<%def name="extrahead()">
    <link rel="stylesheet" href="${pathto('_static/tour.css', 1)}" type="text/css" media="screen" />
    
</%def>

<%def name="prevnextheader()"></%def>


<%def name="sidebar()">

  <div class="sphinxsidebar">
     <div class="sphinxsidebarwrapper">
      <div class="news">

      <h2>Release 0.9.5 is out</h2>
      
      I'm happy to announce that on February, 7 2012 I released 
      <a href="${pathto('misc/download', )}#download">version 0.9.5</a> of
	sqlkit that adds support for sqlalchemy 0.7+ as wel as some minor
        improvements (see
	<a href="/download/Changelog">changelog</a>). 
	
     </div>
     </div>

   </div>
</%def>

${next.body()}
