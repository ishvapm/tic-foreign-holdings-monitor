import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"src"))
from run_analysis import parse,robust_z,concentration,kmeans_latest,anomalies
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.rows=parse()
 def test_official_history(c):c.assertGreater(len(c.rows),8000)
 def test_robust_z(c):c.assertGreater(robust_z(100,list(range(20))),5)
 def test_concentration_bounds(c):
  x=concentration(c.rows)[-1];c.assertGreater(x["hhi"],0);c.assertLessEqual(x["hhi"],1);c.assertGreater(x["effective_number"],1)
 def test_clusters(c):c.assertGreater(len(kmeans_latest(c.rows)),20)
 def test_signals(c):c.assertGreater(len(anomalies(c.rows)),0)
if __name__=="__main__":unittest.main()
