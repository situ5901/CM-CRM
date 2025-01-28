from pymongo import MongoClient
import requests
import time
from datetime import datetime

# MongoDB connection setup
client = MongoClient("mongodb+srv://ceo:m1jZaiWN2ulUH0ux@cluster1.zdfza.mongodb.net/")
db = client['test']
mis_collection = db['mis']

def get_partners_for_phones(phones):
    """Call getPartners API with a batch of phone numbers"""
    api_url = "https://credmantra.com/api/v1/crm/getPartners"
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(
            api_url,
            json={"phones": phones},
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API request failed with status code {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error calling API: {str(e)}")
        return None

def main():
    # Find documents without partner key
    query = {"partner": {"$exists": False}}
    total_docs = mis_collection.count_documents(query)
    
    if total_docs == 0:
        print("No documents found without 'partner' key")
        return
        
    print(f"Found {total_docs} documents without 'partner' key")
    
    # Process in batches of 10
    batch_size = 10
    processed = 0
    failed = 0
    
    # Get cursor for documents without partner
    cursor = mis_collection.find(query, {"phone": 1})
    
    current_batch = []
    for doc in cursor:
        if "phone" not in doc:
            continue
            
        current_batch.append(doc["phone"])
        
        # When batch is full or this is the last document
        if len(current_batch) >= batch_size or processed + len(current_batch) == total_docs:
            print(f"\nProcessing batch of {len(current_batch)} phones...")
            
            # Get partner data for current batch
            partner_data = get_partners_for_phones(current_batch)
            
            if partner_data:
                # Update documents with partner info
                for item in partner_data:
                    if isinstance(item, dict) and "phone" in item and "partner" in item:
                        try:
                            ### Print document before update
                            # doc_before = mis_collection.find_one({"phone": item["phone"]})
                            # print(f"\nBefore update: {doc_before}")
                            result = mis_collection.update_one(
                                {"phone": item["phone"]},
                                {
                                    "$set": {
                                        "partner": item["partner"],
                                        "updatedAt": datetime.now()
                                    }
                                }
                            )

                            # print(item["partner"])
                            if result.modified_count > 0:
                                print(f"Updated partner for phone: {item['phone']}")
                            else:
                                print(f"No update needed for phone: {item['phone']}")
                        except Exception as e:
                            print(f"Error updating document for phone {item['phone']}: {str(e)}")
                            failed += 1
            else:
                failed += len(current_batch)
                
            processed += len(current_batch)
            print(f"Progress: {processed}/{total_docs} documents processed ({failed} failed)")
            
            # Clear batch
            current_batch = []
            
            # Add delay to avoid overwhelming the API
            time.sleep(1)
    
    print(f"\nCompleted processing {processed} documents ({failed} failed)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        print(f"Script error: {str(e)}")
    finally:
        client.close() 