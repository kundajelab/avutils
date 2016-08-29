
def assert_parameter_necessary_for_mode(parameter_name,
                                        parameter, mode_name, mode):
    if (parameter is None):
        raise RuntimeError(
            parameter_name+" is necessary when "+mode_name+" is "+mode)
    
def assert_parameter_irrelevant_for_mode(parameter_name,
                                         parameter, mode_name, mode):
    if (parameter is not None):
        raise RuntimeError(
            parameter_name+" is irrelevant when "+mode_name+" is "+mode)

def unsupported_value_for_mode(mode_name, mode):
   raise RuntimeError("Unsupported value for "+mode_name+": "+str(mode))
