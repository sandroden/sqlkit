## coding: utf-8
<%inherit file="home.mako"/>

<h1>Perché interessa anche alla vostra scuola...</h1>

 <% 
    import os, re 
    files = [f for f in os.listdir('templates_mako/slides') if  re.match('slide_.*mako$', f)] 
 %>
% for f in sorted(files):
  
  <%include file="slides/${f}"/>

% endfor


  

