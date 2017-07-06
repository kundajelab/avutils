from __future__ import print_function
import re
import os
import os.path
import gzip
import shutil
import time
from collections import OrderedDict
import yaml
#configure the yaml package to use OrderedDict
from yaml.resolver import BaseResolver
yaml.add_representer(
    OrderedDict,
    lambda representer, data: representer.represent_dict(data.iteritems()))
yaml.add_constructor(BaseResolver.DEFAULT_MAPPING_TAG,
    lambda constructor, node: OrderedDict(constructor.construct_pairs(node)))
from . import error_messages
from . import util 


def get_file_handle(filename,mode="r"):
    if (re.search('.gz$',filename) or re.search('.gzip',filename)):
        if (mode=="r"):
            mode="rb";
        elif (mode=="w"):
            #I think write will actually append if the file already
            #exists...so you want to remove it if it exists
            if os.path.isfile(filename):
                os.remove(filename);
        return gzip.open(filename,mode)
    else:
        return open(filename,mode) 


def default_tab_seppd(s):
    s = trim_newline(s)
    s = split_by_delimiter(s, "\t")
    return s


def trim_newline(s):
    return s.rstrip('\r\n')


def split_by_delimiter(s, delimiter):
    return s.split(delimiter)


def split_by_tabs(s):
    return split_by_delimiter(s,"\t")


def process_line(line, i, ignore_input_title,
                 transformation, action, progress_update=None):
    if (i > 1 or (ignore_input_title==False)):
        action(transformation(line),i)


def print_progress(progress_update, i, file_name=None):
    if progress_update is not None:
        if (i%progress_update == 0):
            print("Processed "+str(i)+" lines"
                   +str("" if file_name is None else " of "+file_name))


def perform_action_on_each_line_of_file(
    file_handle
    #should be a function that accepts the
    #preprocessed/filtered line and the line number
    , action
    , transformation=default_tab_seppd
    , ignore_input_title=False
    , progress_update=None
    , progress_update_file_name=None):

    i = 0;
    for line in file_handle:
        i += 1;
        process_line(line, i, ignore_input_title,
                     transformation, action, progress_update)
        print_progress(progress_update, i, progress_update_file_name)

    file_handle.close();


def read_rows_into_arr(file_handle):
    if isinstance(file_handle, str):
        file_handle = get_file_handle(file_handle) 
    rows = [trim_newline(line) for line in file_handle]
    return rows 


def read_col_into_arr(file_handle, col=0, title_present=False):
    arr = [];
    def action(inp, line_number):
        arr.append(inp[col]);
    perform_action_on_each_line_of_file(
        file_handle
        , transformation=default_tab_seppd
        , action=action
        , ignore_input_title=title_present
    );
    return arr


def write_matrix_to_file(file_handle, rows, col_names=None, row_names=None):
    if (col_names is not None):
        file_handle.write(("rowName\t" if row_names is not None else "")
                          +"\t".join(col_names)+"\n")
    for i,row in enumerate(rows):
        if (row_names is not None):
            file_handle.write(row_names[i]+"\t")
        stringified_row = [str(x) for x in row];
        to_write = "\t".join(stringified_row)+"\n";
        file_handle.write(to_write);
    file_handle.close();


class TitledMappingIterator(object):

    def __init__(self, titled_mapping):
        """
            Returns an iterator over TitledArrs for
            the keys in titled_mapping.mapping
        """
        self.titled_mapping = titled_mapping;
        self.keys_iterator = iter(titled_mapping.mapping);

    def next(self):
        next_key = self.keys_iterator.next();
        return self.titled_mapping.get_titled_arr_for_key(next_key);


class TitledMapping(object):

    def __init__(self, title_arr, flag_if_inconsistent=False):
        """
            When each key maps to an array, and each index
            in the array is associated with a name.
        """
        self.mapping = OrderedDict() #mapping from name of a key to the values
        self.title_arr = title_arr
        self.col_name_to_index =\
            dict((x,i) for (i,x) in enumerate(self.title_arr))
        self.row_size = len(self.title_arr)
        self.flag_if_inconsistent = flag_if_inconsistent

    def key_presence_check(self, key):
        """
            Throws an error if the key is absent
        """
        if (key not in self.mapping):
            raise RuntimeError("Key "+str(key)
                  +" not in mapping; supported feature names are "
                  +str(self.mapping.keys()))

    def get_arr_for_key(self, key):
        self.key_presence_check(key);
        return self.mapping[key]

    def get_titled_arr_for_key(self, key):
        """
            returns an instance of util.TitledArr which has: get_col(colName) and set_col(colName)
        """
        return TitledArr(self.title_arr, self.get_arr_for_key(key),
                         self.col_name_to_index)

    def add_key(self, key, arr):
        if (len(arr) != self.row_size):
            raise RuntimeError("arr should be of size "
                    +str(self.row_size)+" but is of size "+str(len(arr)))
        if (self.flag_if_inconsistent):
            if key in self.mapping:
                if (str(self.mapping[key]) != str(arr)):
                    raise RuntimeError("Tried to add "+str(arr)
                           +" for key "+str(key)+" but "
                           +str(self.mapping[key])+" already present")
        self.mapping[key] = arr

    def __iter__(self):
        """
            Iterator is over instances of TitledArr!
        """
        return TitledMappingIterator(self)

    def print_to_file(self, file_handle, includeRownames=True):
        write_matrix_to_file(file_handle,
         self.mapping.values(), self.title_arr,
         [x for x in self.mapping.keys()])


class TitledArr(object):

    def __init__(self, title, arr, col_name_to_index=None):
        assert len(title)==len(arr)
        self.title = title
        self.arr = arr
        self.col_name_to_index = col_name_to_index

    def get_col(self, colName):
        assert self.col_name_to_index is not None
        return self.arr[self.col_name_to_index[colName]]

    def set_col(self, colName, value):
        assert self.col_name_to_index is not None
        self.arr[self.col_name_to_index[colName]] = value


SubsetOfColumnsToUseMode = util.enum(set_of_column_names="set_of_column_names",
                                     top_n="top_n")
class SubsetOfColumnsToUseOptions(object):

    def __init__(self, mode=SubsetOfColumnsToUseMode.set_of_column_names,
                       column_names=None, N=None):
        self.mode = mode
        self.column_names = column_names
        self.N = N
        self.integrity_checks()

    def integrity_checks(self):
        if (self.mode == SubsetOfColumnsToUseMode.set_of_column_names):
            error_messages.assert_parameter_irrelevant_for_mode(
                "N", self.N, "subset_of_columns_to_use_mode", self.mode)
            error_messages.assert_parameter_necessary_for_mode(
                "column_names", self.column_names,
                "subset_of_columns_to_use_mode", self.mode)
        elif (self.mode == SubsetOfColumnsToUseMode.top_n):
            error_messages.assert_parameter_irrelevant_for_mode(
                "column_names", self.colum_names,
                "subset_of_columns_to_use_mode", self.mode)
            error_messages.assert_parameter_necessary_for_mode(
                "N", self.N, "subset_of_columns_to_use_mode", self.mode)
        else:
            error_messages.unsupported_value_for_mode("mode", self.mode)


def get_core_titled_mapping_action(subset_of_columns_to_use_options,
                                   content_type,
                                   content_start_index,
                                   subset_of_rows_to_use=None,
                                   key_columns=[0]):
    subset_of_rows_to_use_membership_dict =\
        (dict((x,1) for x in subset_of_rows_to_use)
         if subset_of_rows_to_use is not None else None)
    indices_to_care_about_wrapper = util.VariableWrapper(None)
    def titled_mapping_action(inp, line_number):
        if (line_number==1): #handling of the title
            if subset_of_columns_to_use_options is None:
                column_ordering = inp[content_start_index:]
            else:
                if (subset_of_columns_to_use_options.mode ==
                    SubsetOfColumnsToUseMode.set_of_column_names):
                    column_ordering =\
                     subset_of_columns_to_use_options.column_names
                elif (subset_of_columns_to_use_options.mode ==
                      SubsetOfColumnsToUseMode.top_n):
                    column_ordering =\
                     inp[content_start_index:
                         content_start_index+SubsetOfColumnsToUseMode.top_n]
                else:
                    raise RuntimeError(
                     "Unsupported subset_of_columns_to_use_options.mode: "
                     +str(subset_of_columns_to_use_options.mode))
                indices_lookup = dict((x,i) for (i,x) in enumerate(inp))
                indices_to_care_about_wrapper.var = []
                for label_to_use in column_ordering:
                    indices_to_care_about_wrapper.var.append(
                     indices_lookup[label_to_use])
            return column_ordering
        else:
            #regular line processing
            key = "_".join(inp[x] for x in key_columns)
            #if we aren't skipping this row...
            if (subset_of_rows_to_use_membership_dict is None
                or (key in subset_of_rows_to_use_membership_dict)):
                if (indices_to_care_about_wrapper.var is None):
                    arr_to_add = [content_type(x) for x
                                  in inp[content_start_index:]]
                else:
                    arr_to_add = [content_type(inp[x]) for x
                                  in indices_to_care_about_wrapper.var]
                return key, arr_to_add
            return None #this is a row to skip
    return titled_mapping_action


def read_titled_mapping(file_handle,
                      content_type=float,
                      content_start_index=1,
                      subset_of_columns_to_use_options=None,
                      subset_of_rows_to_use=None,
                      progress_update=None,
                      key_columns=[0]):
    """
        returns an instance of util.TitledMapping.
            util.TitledMapping has functions:
                - get_titled_arr_for_key(key): returns an instance of
                  TitledArr which has: get_col(col_name) and set_col(col_name)
                - get_arr_for_key(key): returns the array for the key
                - key_presence_check(key): throws an error if the key is absent
                Is also iterable! Returns an iterator of TitledArr 
        subset_of_columns_to_use_options:
            instance of SubsetOfColumnsToUseOptions
        subset_of_rows_to_use:
            something that has a subset of row ids to be considered
    """

    titled_mapping_wrapper = util.VariableWrapper(None);
    core_titled_mapping_action = get_core_titled_mapping_action(
                    subset_of_columns_to_use_options=
                        subset_of_columns_to_use_options,
                    content_type=content_type,
                    content_start_index=content_start_index,
                    subset_of_rows_to_use=subset_of_rows_to_use,
                    key_columns=key_columns)

    def action(inp, line_number):
        if (line_number==1): #handling of the title
            column_ordering = core_titled_mapping_action(inp, line_number)
            titled_mapping_wrapper.var = util.TitledMapping(column_ordering)
        else:
            key, arr_to_add = core_titled_mapping_action(inp, line_number)
            if (arr_to_add is not None):
                titled_mapping_wrapper.var.add_key(key, arr_to_add)

    perform_action_on_each_line_of_file(
        file_handle
        ,transformation=default_tab_seppd
        ,action=action)

    return titled_mapping_wrapper.var 


class FastaIterator(object):
    """
        Returns an iterator over lines of a fasta file - assumes each sequence
        spans only one line!
    """
    def __init__(self, file_handle, progress_update=None,
                       progress_update_file_name=None):
        self.file_handle = file_handle
        self.progress_update = progress_update
        self.progress_update_file_name = progress_update_file_name
        self.line_count = 0

    def __iter__(self):
        return self

    def next(self):
        self.line_count += 1
        print_progress(self.progress_update,
                       self.line_count,
                       self.progress_update_file_name)
        #should raise StopIteration if at end of lines
        key_line = trim_newline(self.file_handle.next())
        sequence = trim_newline(self.file_handle.next())
        if (key_line.startswith(">")==False):
            raise RuntimeError("Expecting a record name line that begins "
                               +"with > but got "+str(key_line))
        key = key_line.lstrip(">")
        return key, sequence


class Hdf5BufferedDatasetWriter(object):

    def __init__(self, dataset, buffer_size=10000):
        self.dataset = dataset
        self.written_so_far = 0 
        self.the_buffer = []
        self.buffer_size = buffer_size

    def write(self, entry):
        self.the_buffer.append(entry)
        if (len(self.the_buffer) == self.buffer_size):
            self.flush()

    def write_all(self, entries):
        self.the_buffer.extend(entries)
        if (len(self.the_buffer) > self.buffer_size):
            self.flush()

    def flush(self):
        self.dataset[self.written_so_far:
                     (self.written_so_far+len(self.the_buffer))] =\
                     self.the_buffer
        self.written_so_far += len(self.the_buffer)
        self.the_buffer = []


def batch_execute_hdf5_to_hdf5(input_dataset, output_dataset, batch_action,
                               input_batch_size=10000,
                               output_buffer_size=10000,
                               progress_update=None):
    input_dataset_length = len(input_dataset) 
    start_idx = 0
    hdf5_buffered_writer = Hdf5BufferedDatasetWriter(
                            output_dataset,
                            buffer_size=output_buffer_size)
    while start_idx < input_dataset_length:
        end_idx = min(start_idx+input_batch_size, input_dataset_length)
        input_batch = input_dataset[start_idx:end_idx]
        hdf5_buffered_writer.write_all(batch_action(input_batch))
        if (progress_update is not None):
            if (int(end_idx/progress_update) > int(start_idx/progress_update)):
                print("Processed",end_idx,"items")
        start_idx += input_batch_size
    hdf5_buffered_writer.flush()


def write_to_file(output_file, contents):
    output_file_handle = get_file_handle(output_file, 'w')
    write_to_file_handle(output_file_handle, contents)

def append_to_file(output_file, contents):
    output_file_handle = get_file_handle(output_file, 'a')
    write_to_file_handle(output_file_handle, contents)

def write_to_file_handle(output_file_handle, contents):
    output_file_handle.write(contents)
    output_file_handle.close()


def rename_files(tuples_for_renaming):
    for old_file, new_file in tuples_for_renaming:
        shutil.move(old_file, new_file) 


def load_yaml_if_string(yaml_stuff):
    if (isinstance(yaml_stuff, str)):
        yaml_stuff = yaml.load(get_file_handle(yaml_stuff))
    return yaml_stuff


class FileLockAsDir(object):
    #hacking unix directories to create v. lightweight
    #locking mechanism for reading from files.
    #I need this for when my different threads may
    #not be able to communicate with each other
    #and have no knowledge of each other.
    #...and I really don't want to spin up a db server.
    def __init__(self, file_name, sleep_seconds=5, max_tries=5):

        self.lock_dir_name = (
            util.get_file_name_parts(file_name)\
            .get_transformed_file_path(
                transformation=lambda x: "lockdir_"+x, extension=""))
        lock_acquired = False
        tries = 0

        while (lock_acquired==False):
            print("Trying for "+self.lock_dir_name)
            try:
                os.mkdir(self.lock_dir_name)
                lock_acquired = True
            except OSError as e:
                tries += 1
                if (tries==max_tries):
                    print("Tried and failed acquiring"+
                          self.lock_dir_name+" "+str(tries)+"times")
                    print("Forcibly taking")
                    os.rmdir(self.lock_dir_name)
                time.sleep(sleep_seconds)

    def release(self):
        os.rmdir(self.lock_dir_name)
        print(self.lock_dir_name, "released") 


class BackupForWriteFileHandle(object):
    def __init__(self, file_name):
        """
        Wrapper around a filehandle that
            backs up the file while writing,
            then deletes the backup when close
            is called
        """
        self.file_name = file_name
        self.backup_file_name = file_name+".backup"
        if util.file_exists(self.file_name): 
            os.system("cp "+self.file_name+" "+self.backup_file_name)
        self.output_file_handle = get_file_handle(self.file_name,'w')

    def write(self, *args, **kwargs):
        self.output_file_handle.write(*args, **kwargs)

    def close(self):
        self.output_file_handle.close()
        if (util.file_exists(self.backup_file_name)):
            os.system("rm "+self.backup_file_name)

    def restore(self):
        os.system("cp "+self.backup_file_name+" "+self.file_name)
        os.system("rm "+self.backup_file_name)
        self.output_file_handle.close()
