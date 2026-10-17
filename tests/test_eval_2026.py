"""The 2026 extraction block of section 6 (17 Oct): one annotator is the gold set, the second only gives kappa."""
from skillabus import eval_run as er

SAMPLE = ("ad_id,role,company,title,url,second_annotator,description\n"
          "A,Data Scientist,c,t,u,y,We need Python and SQL for reporting.\n"
          "B,Cloud Engineer,c,t,u,n,Experience with AWS and Terraform is essential.\n"
          "C,Software Engineer,c,t,u,y,Build integrations in Celigo for our platform.\n")
LABELS = ("ad_id,skill_label,in_dictionary,evidence_text,annotator\n"
          "A,Python,y,Python,tompham9016\nA,SQL,y,SQL,tompham9016\n"
          "B,AWS,y,AWS,tompham9016\nB,Terraform,y,Terraform,tompham9016\n"
          "C,Celigo,n,Celigo,tompham9016\n"
          "A,Python,y,Python,nhinguyenuts\n")


def test_2026_block_scores_the_gold_annotator_and_gives_kappa_on_the_shared_ads(tmp_path, monkeypatch):
    (tmp_path / "sample.csv").write_text(SAMPLE, encoding="utf-8")
    (tmp_path / "labels.csv").write_text(LABELS, encoding="utf-8")
    monkeypatch.setattr(er, "ADS_2026", tmp_path / "sample.csv")
    monkeypatch.setattr(er, "AD_SKILLS_2026", tmp_path / "labels.csv")
    res = er.run_2026(("dictionary",))
    assert (res["n_ads"], res["n_labels"], res["n_roles"]) == (3, 5, 3)    # the second annotator's row is not gold
    tier = res["tiers"]["dictionary"]
    assert (tier["all"]["tp"], tier["all"]["fn"]) == (4, 1)                # Celigo is outside the vocabulary
    assert tier["vocabulary"]["recall"] == 1.0
    k = res["kappa"]
    # both second-annotator ads count, C too although the second annotator gave it no row
    assert k["annotators"] == ["tompham9016", "nhinguyenuts"] and k["n_ads"] == 2
    assert k["both_yes"] == 1 and k["a_only"] >= 1 and k["b_only"] == 0


def test_2026_block_says_why_when_the_files_are_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(er, "AD_SKILLS_2026", tmp_path / "none.csv")
    assert er.run_2026(("dictionary",)).startswith("not run")
