# app/constants/dummy.py

from app.models.text import (
    CreateScriptResponse,
    CreateImagePromptsResponse,
    ImagePromptDetail,
)

from app.models.audio import CreateAudioResponse
from app.models.image import CreateImageResponse
from app.models.video import CreateVideoResponse

import random

DUMMY_SCRIPT_RESPONSE = CreateScriptResponse(
    content="Quá trình sinh trưởng của thực vật là một chủ đề thú vị và đầy màu sắc trong thế giới tự nhiên. Khi nhìn ra ngoài, chúng ta thường thấy cây cối vươn mình, nở hoa và ra trái. Nhưng điều gì thực sự diễn ra bên trong những sinh vật này? Hãy cùng khám phá.\n\nSinh trưởng của thực vật bắt đầu từ hạt giống. Một hạt giống chứa tất cả các thông tin di truyền cần thiết để phát triển thành một cây hoàn chỉnh. Khi hạt giống gặp môi trường thuận lợi, như độ ẩm và nhiệt độ thích hợp, nó bắt đầu nảy mầm. Quá trình này giống như một phép màu, khi hạt giống hấp thụ nước và dinh dưỡng từ đất, kích thích sự phát triển của rễ và mầm cây.\n\nRễ cây là bộ phận quan trọng đầu tiên phát triển. Chúng không chỉ giúp cây bám chặt vào mặt đất mà còn hấp thụ nước và khoáng chất cần thiết cho sự phát triển. Khi rễ mạnh mẽ, mầm cây bắt đầu vươn lên, tìm kiếm ánh sáng mặt trời. Ánh sáng là nguồn năng lượng chính cho thực vật, giúp chúng thực hiện quá trình quang hợp.\n\nQuang hợp là một quá trình kỳ diệu, mà qua đó cây cối chuyển đổi ánh sáng mặt trời thành năng lượng. Trong quá trình này, cây hấp thụ carbon dioxide từ không khí và nước từ đất, sau đó sản xuất ra glucose và oxy. Glucose là nguồn năng lượng mà cây sử dụng để phát triển, trong khi oxy được thải ra, cung cấp cho chúng ta không khí trong lành.\n\nKhi cây trưởng thành, nó sẽ trải qua nhiều giai đoạn sinh trưởng khác nhau. Cây sẽ phát triển thêm thân, lá và hoa. Mỗi bộ phận này đóng một vai trò quan trọng trong quá trình sinh trưởng và sinh sản. Thân cây không chỉ hỗ trợ cấu trúc mà còn vận chuyển nước và chất dinh dưỡng giữa các bộ phận. Lá cây, với bề mặt rộng và xanh tươi, là nơi diễn ra quang hợp, cung cấp năng lượng cho toàn bộ cây.\n\nKhi đến giai đoạn trưởng thành, cây sẽ bắt đầu ra hoa. Hoa không chỉ đẹp mắt mà còn là phần quan trọng trong quá trình sinh sản. Chúng thu hút côn trùng thụ phấn, giúp cho quá trình thụ tinh diễn ra. Sau khi thụ tinh, hoa sẽ phát triển thành trái, bên trong chứa hạt giống cho thế hệ cây kế tiếp.\n\nQuá trình sinh trưởng của thực vật không chỉ đơn thuần là sự phát triển của cây mà còn là một chu trình liên kết với môi trường xung quanh. Thực vật tương tác với đất, nước, ánh sáng và khí hậu, tạo thành một hệ sinh thái phong phú. Sự sinh trưởng của thực vật đóng vai trò quan trọng trong việc duy trì sự cân bằng sinh thái, cung cấp thực phẩm, nơi sống và oxy cho các sinh vật khác.\n\nTóm lại, quá trình sinh trưởng của thực vật bắt đầu từ hạt giống và trải qua nhiều giai đoạn khác nhau, từ nảy mầm, phát triển rễ và mầm, đến trưởng thành và ra hoa. Mỗi giai đoạn đều có những chức năng và vai trò quan trọng, không chỉ cho bản thân cây mà còn cho toàn bộ hệ sinh thái. Qua đó, chúng ta thấy được vẻ đẹp và sự kỳ diệu của thế giới thực vật xung quanh mình."
)

DUMMY_IMAGE_PROMPTS_RESPONSE = CreateImagePromptsResponse(
    prompts=[
        ImagePromptDetail(
            prompt="A vibrant outdoor scene depicting various plants and trees, with a focus on their growth processes. Some trees are tall and blooming, while others are budding with flowers and fruits. The background showcases a sunny day with a clear blue sky, and a variety of colors representing different plants in full bloom. ",
            script="Quá trình sinh trưởng của thực vật là một chủ đề thú vị và đầy màu sắc trong thế giới tự nhiên. Khi nhìn ra ngoài, chúng ta thường thấy cây cối vươn mình, nở hoa và ra trái. Nhưng điều gì thực sự diễn ra bên trong những sinh vật này? Hãy cùng khám phá.",
        ),
        ImagePromptDetail(
            prompt="A close-up view of a seed nestled in dark, rich soil. The seed is beginning to germinate, with tiny white roots emerging downwards and a small green shoot pushing upwards. Surrounding the seed are droplets of water and tiny particles of nutrients, illustrating the favorable conditions for germination.",
            script="Sinh trưởng của thực vật bắt đầu từ hạt giống. Một hạt giống chứa tất cả các thông tin di truyền cần thiết để phát triển thành một cây hoàn chỉnh. Khi hạt giống gặp môi trường thuận lợi, như độ ẩm và nhiệt độ thích hợp, nó bắt đầu nảy mầm. Quá trình này giống như một phép màu, khi hạt giống hấp thụ nước và dinh dưỡng từ đất, kích thích sự phát triển của rễ và mầm cây.",
        ),
        ImagePromptDetail(
            prompt="A cross-section illustration of a young plant showing its developing root system. The roots are spread out in the soil, anchoring the plant and absorbing water and minerals. Above the soil, a small green sprout is reaching for sunlight, indicating the plant's growth towards energy.",
            script="Rễ cây là bộ phận quan trọng đầu tiên phát triển. Chúng không chỉ giúp cây bám chặt vào mặt đất mà còn hấp thụ nước và khoáng chất cần thiết cho sự phát triển. Khi rễ mạnh mẽ, mầm cây bắt đầu vươn lên, tìm kiếm ánh sáng mặt trời. Ánh sáng là nguồn năng lượng chính cho thực vật, giúp chúng thực hiện quá trình quang hợp.",
        ),
        ImagePromptDetail(
            prompt="An illustration of photosynthesis in action: a vibrant green leaf with sunlight streaming down on it. The leaf is depicted with small bubbles representing oxygen being released and arrows indicating the intake of carbon dioxide and water. Glucose molecules are also shown being formed within the leaf.",
            script="Quang hợp là một quá trình kỳ diệu, mà qua đó cây cối chuyển đổi ánh sáng mặt trời thành năng lượng. Trong quá trình này, cây hấp thụ carbon dioxide từ không khí và nước từ đất, sau đó sản xuất ra glucose và oxy. Glucose là nguồn năng lượng mà cây sử dụng để phát triển, trong khi oxy được thải ra, cung cấp cho chúng ta không khí trong lành.",
        ),
        ImagePromptDetail(
            prompt="A wide shot of a mature plant with a strong trunk, lush green leaves, and blooming flowers. The trunk is sturdy, with leaves catching sunlight, and flowers attracting various pollinators like bees and butterflies. The scene conveys the plant's role in the ecosystem.",
            script="Khi cây trưởng thành, nó sẽ trải qua nhiều giai đoạn sinh trưởng khác nhau. Cây sẽ phát triển thêm thân, lá và hoa. Mỗi bộ phận này đóng một vai trò quan trọng trong quá trình sinh trưởng và sinh sản. Thân cây không chỉ hỗ trợ cấu trúc mà còn vận chuyển nước và chất dinh dưỡng giữa các bộ phận. Lá cây, với bề mặt rộng và xanh tươi, là nơi diễn ra quang hợp, cung cấp năng lượng cho toàn bộ cây.",
        ),
        ImagePromptDetail(
            prompt="An artistic depiction of flowering plants in a garden, with a variety of colorful flowers in full bloom. The flowers are attracting insects like bees, which are shown pollinating them. This scene emphasizes the importance of flowers in reproduction and biodiversity.",
            script="Khi đến giai đoạn trưởng thành, cây sẽ bắt đầu ra hoa. Hoa không chỉ đẹp mắt mà còn là phần quan trọng trong quá trình sinh sản. Chúng thu hút côn trùng thụ phấn, giúp cho quá trình thụ tinh diễn ra. Sau khi thụ tinh, hoa sẽ phát triển thành trái, bên trong chứa hạt giống cho thế hệ cây kế tiếp.",
        ),
        ImagePromptDetail(
            prompt="An expansive view of a thriving ecosystem with various plants, trees, and wildlife. The image shows how plants interact with their environment, including soil, water sources, and sunlight. A diverse range of species can be seen, illustrating the richness of the ecosystem.",
            script="Quá trình sinh trưởng của thực vật không chỉ đơn thuần là sự phát triển của cây mà còn là một chu trình liên kết với môi trường xung quanh. Thực vật tương tác với đất, nước, ánh sáng và khí hậu, tạo thành một hệ sinh thái phong phú. Sự sinh trưởng của thực vật đóng vai trò quan trọng trong việc duy trì sự cân bằng sinh thái, cung cấp thực phẩm, nơi sống và oxy cho các sinh vật khác.",
        ),
        ImagePromptDetail(
            prompt="A concluding scene summarizing plant growth stages, featuring a timeline-like visual with images of a seed, germination, root development, photosynthesis, flowering, and fruiting. Each stage is labeled and visually distinct, emphasizing the interconnectedness of each phase in the life of a plant.",
            script="Tóm lại, quá trình sinh trưởng của thực vật bắt đầu từ hạt giống và trải qua nhiều giai đoạn khác nhau, từ nảy mầm, phát triển rễ và mầm, đến trưởng thành và ra hoa. Mỗi giai đoạn đều có những chức năng và vai trò quan trọng, không chỉ cho bản thân cây mà còn cho toàn bộ hệ sinh thái. Qua đó, chúng ta thấy được vẻ đẹp và sự kỳ diệu của thế giới thực vật xung quanh mình.",
        ),
    ],
    style="Phổ thông",
)

IMAGE_URLS = [
    "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/images/DALL%C2%B7E%202025-03-23%2016.52.32%20-%20A%20close-up%20view%20of%20a%20seed%20undergoing%20germination%20in%20dark,%20moist%20soil.%20Delicate%20white%20roots%20are%20sprouting%20downward,%20and%20a%20tiny%20green%20shoot%20is%20breaking%20.webp",
    "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/images/DALL%C2%B7E%202025-03-23%2016.52.40%20-%20Root%20System%20Development_%20A%20cross-section%20of%20soil%20revealing%20a%20young%20plant%20with%20an%20intricate%20network%20of%20roots%20spreading%20out%20in%20different%20directions.%20The.webp",
    "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/images/DALL%C2%B7E%202025-03-23%2016.52.49%20-%20Photosynthesis%20Process_%20A%20vibrant,%20wide%20shot%20of%20a%20mature%20plant%20with%20large%20green%20leaves%20absorbing%20sunlight.%20Sunlight%20streams%20down%20clearly%20onto%20the%20plan.webp",
    "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/images/DALL%C2%B7E%202025-03-23%2016.52.53%20-%20Plant%20Growth%20Stages_%20A%20horizontal%20series%20of%20four%20connected%20panels%20showing%20the%20stages%20of%20plant%20growth.%20First%20panel_%20a%20seed%20in%20the%20soil.%20Second%20panel_%20a.webp",
    "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/images/DALL%C2%B7E%202025-03-23%2016.53.00%20-%20Flowering%20Process_%20A%20close-up%20of%20a%20colorful%20flower%20blooming%20on%20a%20mature%20plant.%20The%20petals%20are%20vibrant%20and%20detailed,%20with%20visible%20reproductive%20parts%20in.webp",
    "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/images/DALL%C2%B7E%202025-03-23%2016.53.09%20-%20Fruiting%20and%20Seed%20Dispersal_%20A%20dynamic%20scene%20of%20a%20ripe%20fruit%20hanging%20from%20a%20tree%20branch,%20with%20part%20of%20the%20fruit%20cut%20open%20to%20clearly%20show%20the%20seeds%20ins.webp",
    "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/images/DALL%C2%B7E%202025-03-23%2016.53.27%20-%20Ecosystem%20Interaction_%20A%20wide,%20vibrant%20landscape%20showing%20diverse%20plant%20species%20in%20different%20growth%20stages%20%E2%80%94%20some%20flowering,%20some%20bearing%20fruit.%20Insect.webp",
    "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/images/DALL%C2%B7E%202025-03-23%2016.53.31%20-%20Ecological%20Balance_%20An%20overview%20illustration%20of%20a%20thriving%20ecosystem%20with%20plants,%20animals,%20and%20natural%20elements%20like%20water%20and%20sunlight.%20Plants%20are%20sh.webp",
]

AUDIO_URLS = [
    "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/audio/ffbca4e3617249949181fd96eb5c6a02.mp3",
    "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/audio/fd256acf98fd4c6881bf993e73e08a0e.mp3",
]


# Cycling randomizer to avoid repetition
class CyclicRandomizer:
    def __init__(self, items):
        self.items = list(items)
        self.current_items = []
        self._shuffle_items()

    def _shuffle_items(self):
        self.current_items = list(self.items)
        random.shuffle(self.current_items)

    def get_next(self):
        if not self.current_items:
            self._shuffle_items()
        return self.current_items.pop()


# Initialize randomizers
_image_randomizer = CyclicRandomizer(IMAGE_URLS)
_audio_randomizer = CyclicRandomizer(AUDIO_URLS)


# Get random image response and audio response with cycling
def get_dummy_image_response():
    # return CreateImageResponse(image_url=_image_randomizer.get_next())
    return CreateImageResponse(
        image_url="https://png.pngtree.com/png-vector/20190223/ourmid/pngtree-vector-picture-icon-png-image_695350.jpg"
    )


def get_dummy_audio_response():
    return CreateAudioResponse(
        audio_url=_audio_randomizer.get_next(), audio_duration=300
    )


def get_dummy_video_response():
    return CreateVideoResponse(
        video_url="https://vision-forge.sgp1.cdn.digitaloceanspaces.com/videos/0277518363c24c4c9af68cc968a45f25.mp4",
    )


# Static instances for backward compatibility
DUMMY_IMAGE_RESPONSE = get_dummy_image_response()
DUMMY_AUDIO_RESPONSE = get_dummy_audio_response()
DUMMY_VIDEO_RESPONSE = CreateVideoResponse(
    video_url="https://vision-forge.sgp1.cdn.digitaloceanspaces.com/videos/0277518363c24c4c9af68cc968a45f25.mp4",
)
