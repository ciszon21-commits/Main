assert doc.Objects.Count == 0 and not doc.Modified
workspace.ParentWindow.Size = drawing.Size(500, workspace.ParentWindow.Size.Height)
selector = workspace.GetType().GetField('selector', flags).GetValue(workspace)
selector.Focus()
Rhino.RhinoApp.Wait()
read_state()
