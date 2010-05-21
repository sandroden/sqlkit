.. _backward_incompatibilities:

=================================
Backward Incompatibilities
=================================


From version 0.8.6 (first public release) I keep track of backward
incompatibilities:

0.8.7
=====

:Table:
  
  *  ``self.current`` points to ``self.get_current_obj()``, no longer
     ``get_selected_obj()``

  *  button-press-event now has one more argument: treeview. This is
     necessary due to the fact that table now have views and t.treeview only
     points to the main view's treeview.

:Hooks: 

   arguments in hooks of related widgets where not as documented: a hook on
   a sqlwidget acting on a related  widget would receive the related widget
   as first argument rather that the main one. Look at the the following case::
   
     lay = """
	user
	o2m=addresses
     """
     class Hook(object):
	def on_change_value__addresses__domain(self, sqlwidget, field_name, value, fkvalue):
	   pass

     m = SqlMask(table=User,... hooks=Hook())
     m_address = m.related.addresses
     
   the hook instance will reveive ``m`` as argument where previously
   received ``m_addresses``


