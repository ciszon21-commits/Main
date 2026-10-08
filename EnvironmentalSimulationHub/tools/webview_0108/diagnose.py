test = sc.sticky['ESH_WEBVIEW_0108']; browser = test['browser']
test['dom_task'] = browser.ExecuteScriptAsync('return JSON.stringify({title:document.title,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,text:document.body.innerText,rangeRows:document.querySelectorAll("tbody tr").length,bg:getComputedStyle(document.body).backgroundColor,href:location.href});')
print(str(browser.DocumentTitle))
