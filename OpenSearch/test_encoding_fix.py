
def test_fix():
    # The garbled string from user
    s = "³æ¦ì©Î¤H­û" 
    
    encodings = ['latin1', 'cp1252', 'iso-8859-1']
    targets = ['big5', 'utf-8', 'gbk']
    
    print(f"Original: {s}")
    print("-" * 20)
    
    for enc in encodings:
        for tgt in targets:
            try:
                # Try to reverse the mojibake: encode to bytes using the 'wrong' encoding (e.g. latin1)
                # then decode using the 'correct' encoding (e.g. big5)
                b = s.encode(enc)
                decoded = b.decode(tgt)
                print(f"{enc} -> {tgt}: {decoded}")
            except Exception as e:
                pass
                # print(f"{enc} -> {tgt}: Failed ({e})")

if __name__ == "__main__":
    test_fix()
