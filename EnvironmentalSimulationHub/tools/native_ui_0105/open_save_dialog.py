dialog_path = os.path.join(root,'samples/native_ui_0105/cancel_probe.json')
assert not os.path.exists(dialog_path)
def show_dialog():
    dialog = forms.SaveFileDialog()
    dialog.FileName = dialog_path
    dialog.Filters.Add(forms.FileFilter('分析資料 JSON','.json'))
    result = dialog.ShowDialog(panel)
    report={'pid':identity['pid'],'result':str(result),'file_created':os.path.exists(dialog_path),
            'scope':'Native Eto save-dialog cancellation only; production export button not exercised'}
    with open(os.path.join(root,'docs/evidence/native_ui_0105/save_dialog_result.json'),'w',encoding='utf-8') as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
forms.Application.Instance.AsyncInvoke(show_dialog)
print(json.dumps({'scheduled':'native_save_dialog_cancel','pid':identity['pid']}))
