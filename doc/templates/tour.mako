## coding: utf-8
<%inherit file="layout.mako"/>

<%def name="extrahead()">
    <link rel="stylesheet" href="${pathto('_static/tour.css', 1)}" type="text/css" media="screen" />
    <script type="text/javascript" src="${pathto('_static/preview.js', 1)}"></script>
</%def>

<%def name="sidebar()">

  <div class="sphinxsidebar">
     <div class="sphinxsidebarwrapper">
      <div class="news">

      <h2>Release 0.9 beta is out</h2>
      
      I'm proud to announce that on August, 6 2010 I released 
      <a href="${pathto('misc/download', )}#download">version 0.9beta</a> of
      sqlkit that adds a huge quantity of new features and bug fixes. 
	
      It will stay in beta stage till the end of August.

     </div>
     </div>

   </div>
</%def>

${next.body()}
