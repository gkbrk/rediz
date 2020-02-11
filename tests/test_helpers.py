from rediz.client import Rediz
from threezaconventions.crypto import random_key
import json, os, uuid
import numpy as np

from rediz.rediz_test_config import REDIZ_TEST_CONFIG
# python -m pytest tests/test_helpers.py ; cat tmp_helpers.json


def test_cdf_invcdf():
    normcdf = Rediz._normcdf_function()
    norminv = Rediz._norminv_function()
    for x in np.random.randn(100):
        x1 = norminv(normcdf(x))
        assert abs(x-x1)<1e-4

def test_mean_percentile():
    zscores = np.random.randn(100)
    normcdf = Rediz._normcdf_function()
    norminv = Rediz._norminv_function()
    p = [ normcdf(z) for z in zscores ]
    avg_p = Rediz._zmean_percentile(p)
    implied_avg = norminv(avg_p)
    actual_avg = np.mean(zscores)
    assert abs(implied_avg-actual_avg)<1e-4


def dump(obj,name="tmp_helpers.json"):
    json.dump(obj,open(name,"w"))

def test_various_fake_and_real():
    rdz_fake = Rediz()
    rdz_real = Rediz(**REDIZ_TEST_CONFIG)
    for rdz in [rdz_fake,rdz_real]:
        do_test_exists_delete(rdz)
        do_test_assert_not_in_reserved(rdz)
        do_test__is_valid_key(rdz)
        do_test__is_valid_name(rdz)


def test__streams_support():
    rdz = Rediz(decode_responses=True)  # Use fakeredis
    assert rdz._streams_support()==False, "Test failed because now fakeredis supports streams?!"

def random_name():
    return random_key()+'.json'

def test_card_fake():
    rdz = Rediz()
    assert rdz.card()==0
    title = rdz.random_title()
    rdz.set(value="32",**title)
    assert rdz.card()==1
    del_count = rdz.delete(**title)
    assert del_count>0
    leftover = rdz.client.smembers(rdz._NAMES)
    assert rdz.card() == 0
    assert not leftover

def test_card_real():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    num = rdz.card()
    title = rdz.random_title()
    rdz.set(value=143,**title)
    assert rdz.card()==num+1
    rdz.delete(**title)
    assert rdz.card()==num


def do_test_exists_delete(rdz):
    title = {"name":"d7ec2edb-d045-490e-acbd-7a05122d930e.json","write_key":"3e68a4e0-a827-4462-a714-676aa575802c"}
    name = title["name"]
    rdz._delete_implementation(name) # In case it is left over from previous
    assert rdz.exists(name)==0
    set_res = rdz._pipelined_set(names = [name], values=["10"], write_keys=[ title["write_key"]], budgets=[1])
    exists_res = rdz.exists(name)
    #dump({"exists_res":exists_res,"set_res":set_res})
    assert exists_res==1
    delete_res = rdz.delete(**title)
    assert delete_res>0
    name = title["name"]
    assert rdz.exists(name)==0

def do_test_assert_not_in_reserved(rdz):
    okay_examples     = ["dog:prediction.json","cat:history.json"]
    has_bad_examples  = ["prediction::mine.json","okay.json"]
    rdz.assert_not_in_reserved_namespace(okay_examples)
    try:
        rdz.assert_not_in_reserved_namespace(has_bad_examples)
    except:
        return True
    assert False==True

def do_test__is_valid_key(rdz):
    s = str(uuid.uuid4())
    assert rdz.is_valid_key(s), "Thought "+s+" should be valid."
    assert rdz.is_valid_key("too short")==False, "Thought "+s+" should be invalid"

def do_test__is_valid_name(rdz):
    s = 'dog-7214.json'
    assert rdz.is_valid_name(s), "oops"
    for s in ["25824ee3-d9bf-4923-9be7-19d6c2aafcee.json"]:
        assert rdz.is_valid_name(s),"Got it wrong for "+s

def test_coerce_inputs():
    names, values, write_keys, budgets = Rediz.coerce_inputs(name="dog",value="8",write_key="aslf",budget=1, names=None, values=None, write_keys=None)
    assert names[0]=="dog"
    assert values[0]=="8"
    names, values, write_keys, budgets = Rediz.coerce_inputs(names=["dog","cat"],value="8",write_key="aslf",name=None, values=None, write_keys=None)
    assert names[0]=="dog"
    assert values[1]=="8"
    assert write_keys[1]=="aslf"
    names, values, write_keys, budgets = Rediz.coerce_inputs(names=["dog","cat"],value="12",write_keys=["aslf","blurt"],budget=1, name=None, values=None, write_key=None)
    assert names[0]=="dog"
    assert values[1]=="12"
    assert write_keys[1]=="blurt"
    assert budgets[1]==1
    names, values, write_keys, budgets = Rediz.coerce_inputs(names=[None,None],value="me",write_keys=["aslf","blurt"],name=None, values=None, write_key=None, budget=2)
    assert names[0] is None
    assert values[1]=="me"
    assert budgets[1]==2

def test_coerce_outputs():
    execution_log = {"executed":[ {"name":None,"ndx":1, "write_key":"123"},
                                    {"name":"bill2","ndx":2, "write_key":None},
                                    {"name":"sally0","ndx":0, "write_key":"12"}
                                ],
                    "rejected":[ {"name":None,"ndx":5, "write_key":None},
                                {"name":"bill17","ndx":6, "write_key":None},
                                {"name":"sally23","ndx":4, "write_key":None}
                                ]
                    }
    out = Rediz._coerce_outputs(execution_log)
