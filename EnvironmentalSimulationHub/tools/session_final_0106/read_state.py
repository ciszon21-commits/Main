state = read_state()
json.dump(state,open(os.path.join(evidence,'current_state.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
