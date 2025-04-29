# newspaper_delivery_agent.py

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# Azure Inference client imports
import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage
from azure.core.credentials import AzureKeyCredential

# Assume you already know the real house delivery sequence (fixed)
house_papers_list = [
    "Hindu",
    "TOI, ET",
    "TOI",
    "TOI",
    "Prajavani",
    "TOI (2nd floor)", 
    "Vijayavani, Indian Express",
    "TOI",
    "Prajavani (Taranga)",
    "VK, TOI (Book)",
    "VK",
    "Vijayavani, Deccan",
    "TOI, Prajavani",
    "ET, Hindu",
    "Hindu, ET",
    "VK",
    "VK, Hindu",
    "Patrika",
    "TOI",
    "TOI, VK, Hindu",
    "South India times (new sri ram)",
    "VK",
    "ET, Mirror",
    "TOI",
    "Salar",
    "TOI, Vijayavani",
    "TOI, Vijayavani",
    "Deccan, Salar",
    "TOI (Church)",
    "TOI, TOI, Patrika, Patrika, Deccan, Patrika",
    "TOI",
    "Prajavani",
    "VK (Sun-Praja)",
    "VK",
    "Hindu, TOI",
    "Mirror, TOI",
    "TOI",
    "VK",
    "Deccan, Hindu, TOI",
    "TOI, VK (Sat - Bodhi)",
    "Patrika",
    "TOI",
    "TOI",
    "Hindu",
    "Vijayavani",
    "Deccan",
    "Hindu",
    "TOI",
    "TOI",
    "TOI, Prajavani, Mirror",
    "Prajavani",
    "VK",
    "Deccan, VK",
    "Vijayavani",
    "VK",
    "Mirror, TOI",
    "Salar, Deccan, Hindu",
    "Mirror, TOI (Sun - Deccan)",
    "Malayalam (Malabar)",
    "Deccan",
    "TOI, Mirror",
    "Prajavani",
    "Hindu, VK",
    "Prajavani, Kannada Prabha",
    "Hindu, ET (2nd floor)",
    "TOI",
    "TOI, ET, Vijayavani",
    "TOI",
    "TOI, Patrika",
    "TOI",
    "Vijayavani, Vijayavani",
    "Tamil (Thanti), Deccan",
    "TOI",
    "Vijayavani",
    "VK",
    "TOI (New Red Gate)",
    "TOI (New Masjid)",
    "TOI and ET (beside masjid)",
    "Deccan",
    "TOI, VK",
    "Vijayavani",
    "Prajavani, Hindu",
    "Prajavani, Prajavani",
    "Vijayavani",
    "Prajavani",
    "VK",
    "Tamil (Thanti), Kannada Prabha",
    "Hindu"
]

# Create dynamic delivery points based on house list
delivery_points = {i+1: f"House {i+1}: {paper}" for i, paper in enumerate(house_papers_list)}

# Dummy locations to simulate distance matrix
locations = [(i, i*2) for i in range(len(delivery_points) + 1)]  # Simple locations, not real GPS

def create_distance_matrix(locations):
    size = len(locations)
    matrix = {}
    for from_node in range(size):
        matrix[from_node] = {}
        for to_node in range(size):
            if from_node == to_node:
                matrix[from_node][to_node] = 0
            else:
                matrix[from_node][to_node] = (
                    abs(locations[from_node][0] - locations[to_node][0]) +
                    abs(locations[from_node][1] - locations[to_node][1])
                )
    return matrix

def solve_vrp(distance_matrix):
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        return distance_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        print("No solution found!")
        return

    index = routing.Start(0)
    route = []
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    route.append(manager.IndexToNode(index))
    return route

def generate_delivery_summary(completed_deliveries, total_distance_km, total_time_minutes, papers_collected_summary):
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import UserMessage
    from azure.core.credentials import AzureKeyCredential

    # 🔥 Load from environment variable
    azure_key = os.getenv("AZURE_INFERENCE_KEY")
    if not azure_key:
        raise ValueError("AZURE_INFERENCE_KEY environment variable not set.")

    client = ChatCompletionsClient(
        endpoint="https://models.inference.ai.azure.com",
        credential=AzureKeyCredential(azure_key)
    )

    paper_list = ', '.join(sorted(papers_collected_summary)) if papers_collected_summary else "various newspapers"

    prompt = (
    f"Imagine you are a motivational coach writing a short, energetic message for a newspaper delivery agent.\n\n"
    f"- They woke up at 5 AM to start their day.\n"
    f"- They delivered {completed_deliveries} newspaper deliveries.\n"
    f"- They carried newspapers including: {paper_list}.\n"
    f"- They walked, climbed stairs, and covered a distance of {total_distance_km} km.\n"
    f"- They completed all deliveries within {total_time_minutes} minutes.\n"
    f"- Highlight their hard work, consistency, discipline, and early morning dedication.\n"
    f"- Make them feel proud of their effort.\n"
    f"- End with one inspiring quote about hustle, consistency, or success.\n\n"
    f"Write the message in an energetic, friendly, and short tone, like a quick text to a friend. No email tone."
    )

    response = client.complete(
        messages=[UserMessage(content=prompt)],
        model="Phi-3-small-8k-instruct",
        temperature=0.7,
        max_tokens=300,
        top_p=0.95,
    )

    return response.choices[0].message.content



def delivery_simulation(route):
    print("\nOptimized delivery order:\n")
    for idx, location_idx in enumerate(route[1:], start=1):  # skip depot
        print(f"{idx}. {delivery_points.get(location_idx, 'Unknown Location')}")

    completed = []
    print("\nStart marking deliveries:\n")
    for location_idx in route[1:]:
        if location_idx == 0:
            continue  # Ignore returning to depot
        mark = input(f"Mark delivery at [{delivery_points.get(location_idx, 'Unknown Location')}] as done? (y/n): ")
        if mark.lower() == 'y':
            completed.append(location_idx)

    print("\n--- Delivery Summary ---")
    print(f"Total deliveries assigned: {len(route) - 2}")  # -2 because start and end at depot
    print(f"Deliveries completed: {len(completed)}")
    print(f"Time saved estimate: {15 + len(completed) * 2}%")  # Dummy estimate

    # Generate AI-powered positive message
    generate_delivery_summary(len(completed))

def main():
    distance_matrix = create_distance_matrix(locations)
    route = solve_vrp(distance_matrix)
    if route:
        delivery_simulation(route)

if __name__ == "__main__":
    main()
