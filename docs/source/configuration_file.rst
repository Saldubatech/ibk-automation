Cervino Application Configuration file
*****************************************


The Cervino Application uses a configuration file with [YAML](https://en.wikipedia.org/wiki/YAML) format.

The complete configuration, with its default values  and a brief explanation is:

.. code-block:: YAML

  cervino:
    app_id: cervino # The name of the application
    batch_prefix: order_batch # The prefix to use in naming the batch of orders
    data_dir: '/Users/jmp/.cervino' # The folder where the internal database will be stored
    log_file_name: logging.yml # The name of the logging configuration to use.

  input:
    sheet_name: Movements # The name of the sheet in the input file to use if it is an excel file

  output:
    output_dir: "." # The directory where to place the output file
    file_prefix: "cervino_command_output" # The name of the output file
    file_name: "cervino_command_output.xlsx"  # if provided `file_prefix` is ignored
    # Names of the output sheets
    inputs_sheet: inputs
    known_sheet: known
    updated_sheet: updated
    missing_sheet: missing
    movement_sheet: movement
    error_sheet: errors

  db:
    storage_name: cervino.db # name of the file to contain the internal information

  tws:
    port: 7497  # The port where the TWS API is listening
    host: 'localhost' # The host where the TWS API is listening


