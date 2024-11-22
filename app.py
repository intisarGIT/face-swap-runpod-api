import gradio as gr
import insightface
from insightface.app import FaceAnalysis

assert insightface.__version__ >= '0.7'

def prepare_app():
    app = FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=0, det_size=(640, 640))
    swapper = insightface.model_zoo.get_model('inswapper_128.onnx', download=True, download_zip=True)
    return app, swapper

def sort_faces(faces):
    return sorted(faces, key=lambda x: x.bbox[0])

def get_face(faces, face_id):
    try:
        if len(faces) < face_id or face_id < 1:
            raise gr.Error(f"The image includes only {len(faces)} faces, however, you asked for face {face_id}")
        return faces[face_id-1]
    except Exception as e:
        raise gr.Error(f"An error occurred: {str(e)}")

app, swapper = prepare_app()

def swap_faces(sourceImage, sourceFaceIndex, destinationImage, destinationFaceIndex):
    """Swaps faces between the source and destination images based on the specified face indices."""
    faces = sort_faces(app.get(sourceImage))
    source_face = get_face(faces, sourceFaceIndex)
    
    res_faces = sort_faces(app.get(destinationImage))
    res_face = get_face(res_faces, destinationFaceIndex)

    result = swapper.get(destinationImage, res_face, source_face, paste_back=True)
    return result

gr.Interface(
    swap_faces, 
    [
        gr.Image(label="Source Image (the image with the face that you want to use)"), 
        gr.Number(precision=0, value=1, label='Source Face Position', info='In case there are multiple faces on the image specify which should be used from the left, starting at 1'), 
        gr.Image(label="Destination Image (the image with the face that you want to replace)"), 
        gr.Number(precision=0, value=1, label='Destination Face Position', info='In case there are multiple faces on the image specify which should be replaced from the left, starting at 1')
    ],
    gr.Image(),
    examples=[
        ['./examples/rihanna.jpg', 1, './examples/margaret_thatcher.jpg', 3],
        ['./examples/game_of_thrones.jpg', 5, './examples/game_of_thrones.jpg', 4],
    ],
    theme=gr.themes.Base(),
    title="Face Swapper App 🔄",
    description="🌀 This app allows you to swap faces between images. <br>➡️ Upload a source image and a destination image, and specify the positions of the faces you'd like to swap! <br>⚡️ Try it out quickly by using the examples below. <br>💡 At [Dentro](https://dentro-innovation.com), we help you to discover, develop and implement AI within your organisation! <br>📖 The original authors of the face swap model can be found [here](https://github.com/deepinsight/insightface/blob/master/examples/in_swapper/README.md).<br>❤️ Feel free to like or duplicate this space!",
    # thumbnail='./examples/rihatcher.jpg'
).launch()
