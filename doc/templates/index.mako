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

      <h2>Release 0.9 is out</h2>
      
      I'm happy to announce that on September, 8 2010 I released 
      <a href="${pathto('misc/download', )}#download">version 0.9</a> of
	sqlkit that adds a huge quantity of new features and bug fixes (see 
	<a href="/download/Changelog">changelog</a>). This release works
      with sqlalchemy 0.5 and 0.6 that is now a fully supported release.
	
     </div>
     </div>

   </div>
</%def>

<dix class="promo">
<div id="box1">
   <h1>Sqledit for end users</h1>

   <b>The easiest possible way to browse the data of your database</b>
   
   <p>
   You can customize the way data are presented in a very simple way. The
   ideal tool to edit your personal databases or to browse data of an
   application you're developing with other languages/tools.
   
   <p>
     Filtering data has never been so easy, no SQL knowledge required. 
   <a href="${pathto('misc/sqledit')}">Read more...</a>
   </div>
   <div id="box2">
   <h1>Sqlkit for Python developers</h1>

   <b>The power of a greak framework to create any rich application.</b>
   <p>
     Sqlkit provides 2 widgets to edit data as form or table. It's
     based on PyGTK and sqlalchemy to provide maximum flexibility. 
   <p>
     Key points are the way to design form layout with relationship,
     completions, validation and filter capabilities that can be done w/o
     any effort. More than 80 examples ready to use!
   <a href="${pathto('sqlkit/tour')}">Read more...</a>
   </div>
</div>
