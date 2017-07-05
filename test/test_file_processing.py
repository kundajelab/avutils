import unittest
import avutils.file_processing as fp
import numpy as np
import os

class TestFileProcessing(unittest.TestCase):

    def setUp(self):
        self.input_file_name = "input.h5"
        self.output_file_name = "output.h5"

    def test_batch_execute_hdf5_to_hdf5(self):
        import h5py
        inp_arr = np.arange(300).reshape(100,3)
        input_dataset = h5py.File(self.input_file_name).create_dataset(
                         'input', data=inp_arr)
        output_dataset = h5py.File(self.output_file_name).create_dataset(
                         'output', (100,3))
        def batch_action(input_batch):
            return input_batch+1 
        fp.batch_execute_hdf5_to_hdf5(
            input_dataset=input_dataset,
            output_dataset=output_dataset,
            batch_action=batch_action,
            input_batch_size=10,
            output_buffer_size=100,
            progress_update=50)  

        np.testing.assert_equal(np.array(output_dataset),inp_arr+1)

    def tearDown(self):
        os.remove(self.input_file_name)
        os.remove(self.output_file_name)
        
