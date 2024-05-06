from os.path import dirname, join

import numpy as np

from runtime import ThreadedRuntime
from utils import visualize_bboxes, preprocess_image

if __name__ == '__main__':
    _here = dirname(__file__)
    artifacts_path = join(_here, '..', 'artifacts')

    lib_path = join(artifacts_path, 'libRuntimeLibrary.so')
    onnx_path1 = join(artifacts_path, 'face-locator.onnx')
    onnx_path2 = join(artifacts_path, 'object-detector.onnx')
    image_path = join(artifacts_path, 'image.jpg')

    runtime1 = ThreadedRuntime(lib_path)
    runtime2 = ThreadedRuntime(lib_path)

    rt_name = runtime1.name
    print(f'Runtime name: {rt_name}')

    rt_version = runtime1.version
    print(f'Runtime version: {rt_version}')

    for runtime, model_path in [(runtime1, onnx_path1), (runtime2, onnx_path2)]:
        # Initialize the runtime
        runtime.initialize()
        # Load the model
        runtime.load_model(model_path)

    # prepare the input_tensors
    model1_image = preprocess_image(image_path, 320, 240, 127, 128)
    model2_image = preprocess_image(image_path, 320, 320, 0, 1)
    model1_tensors = {'image-': model1_image,
                      'nms_sensitivity-': np.array([0.5], dtype='float32')}
    # The second model has an additional input tensor: a mask
    model2_tensors = {'image-': model2_image,
                      'nms_sensitivity-': np.array([0.5], dtype='float32'),
                      'mask-': np.ones((320, 320), dtype='bool')}

    # Run both models in parallel, then wait for their results
    runtime1.inference(model1_tensors)
    runtime2.inference(model2_tensors)
    model1_outputs = runtime1.get_last_result()
    model2_outputs = runtime2.get_last_result()

    # Visualize the results
    visualize_bboxes(image_path, list(model1_outputs.values())[0], 320, 240)
    visualize_bboxes(image_path, list(model2_outputs.values())[0], 320, 320)

    # Clean up the resources
    for runtime in [runtime1, runtime2]:
        runtime.inference_cleanup()
        runtime.destroy()
        runtime.stop_thread()
    print('Exiting.')