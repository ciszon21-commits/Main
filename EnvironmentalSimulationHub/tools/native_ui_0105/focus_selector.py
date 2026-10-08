selector = workspace.GetType().GetField('selector', flags).GetValue(workspace)
selector.Focus()
Rhino.RhinoApp.Wait()
read_state()
